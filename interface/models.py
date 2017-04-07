import os
import shutil
import subprocess
from pathlib import Path

import django_rq
from django.conf import settings
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.db import models
from github import UnknownObjectException
from social.apps.django_app.default.models import UserSocialAuth

from interface.tasks import process_wiki
from interface.utils import get_github


class UserProxy(User):
    class Meta:
        proxy = True

    def get_auth(self):
        try:
            data = UserSocialAuth.objects.filter(user=self).values_list('extra_data')[0][0]
        except:
            return None

        username = data['login']
        password = data['access_token']
        return (username, password)


class Repo(models.Model):
    user = models.ForeignKey(UserProxy, related_name='repos')
    full_name = models.TextField(unique=True)
    webhook_id = models.IntegerField(null=True, blank=True)
    is_private = models.BooleanField(default=True)

    wiki_branch = models.TextField(default='master')

    disabled = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.full_name

    def get_absolute_url(self):
        return reverse('repo_detail', kwargs={'full_name': self.full_name})

    @property
    def clone_url(self):
        return 'https://github.com/{}.git'.format(self.full_name)

    def soft_delete(self):
        self.disabled = True
        self.remove_webhook()

    def remove_webhook(self):
        if not settings.DEBUG:
            g = get_github(self.user)
            grepo = g.get_repo(self.full_name)

            try:
                hook = grepo.get_hook(self.webhook_id)
                hook.delete()
            except UnknownObjectException:
                pass

        self.webhook_id = None
        self.save()

    def user_is_collaborator(self, user):
        if not user.is_authenticated():
            return False
        if self.user == user or user.is_staff:
            return True
        g = get_github(user)
        grepo = g.get_repo(self.full_name)
        guser = g.get_user(user.username)
        return grepo.has_in_collaborators(guser)

    def add_webhook(self, request):
        if settings.DEBUG:
            self.webhook_id = 123
        else:
            g = get_github(self.user)
            grepo = g.get_repo(self.full_name)

            hook = grepo.create_hook(
                'web',
                {
                    'content_type': 'json',
                    'url': request.build_absolute_uri(reverse('webhook')),
                    'secret': settings.WEBHOOK_SECRET
                },
                events=['push'],
                active=True
            )
            self.webhook_id = hook.id

        self.save()

    @property
    def directory(self):
        return 'tmp/{}'.format(self.full_name)

    def clean_directory(self):
        if os.path.exists(self.directory):
            shutil.rmtree(self.directory)

    def clone(self, auth):
        clone_url = self.clone_url
        clone_url = clone_url.replace('github.com', '{}:{}@github.com'.format(*auth))
        if not os.path.exists('tmp'):
            os.makedirs('tmp')

        self.clean_directory()

        directory = self.directory

        subprocess.call([
            'git', 'clone', clone_url, self.directory
        ])
        subprocess.call([
            'git', '--git-dir=%s/.git' % directory, '--work-tree=%s' % directory, 'fetch', clone_url
        ])
        subprocess.call([
            'git', '--git-dir=%s/.git' % directory, '--work-tree=%s' % directory, 'checkout', self.wiki_branch
        ])


    def enqueue(self):
        django_rq.enqueue(process_wiki, self.id)

    def parse_fs(self):
        # Walk through each file in the filesystem
        # Create/Delete/Update Documents

        p = Path(self.directory)

        acceptable_filetypes = ('md', 'txt')

        def parse_dir(dir):
            for x in dir.iterdir():
                full_path = str(x)
                path, filename = full_path.rsplit('/', maxsplit=1)
                if x.is_dir() and filename != '.git':
                    parse_dir(x)
                else:
                    ext = ''
                    if '.' in filename:
                        _, ext = filename.rsplit('.', maxsplit=1)
                    with x.open() as f:
                        body = f.read()
                        # TODO: Add support for very large files (chunking?)
                    if ext in acceptable_filetypes:
                        path = path.replace(self.directory, '')
                        Document(
                            repo=self,
                            path=path,
                            filename=filename,
                            body=body
                        )

        parse_dir(p)

    class Meta:
        ordering = ['full_name']


class Document(models.Model):
    repo = models.ForeignKey(Repo)
    path = models.TextField()
    filename = models.TextField()
    body = models.TextField(blank=True)

    def __str__(self):
        return '{}/{}'.format(self.path, self.filename)
