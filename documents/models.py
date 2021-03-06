from django.db import models
from django.urls import reverse


class Document(models.Model):
    FILE_TYPES = ('md', 'txt')

    repo = models.ForeignKey('interface.Repo', related_name='documents')
    path = models.TextField()
    filename = models.TextField()
    body = models.TextField(blank=True)
    commit_date = models.DateTimeField()

    def __str__(self):
        return self.full_path

    @property
    def full_path(self):
        return '{}/{}'.format(self.path, self.filename)

    @property
    def github_view_link(self):
        return 'https://github.com/{0}/blob/{1}{2}'.format(self.repo.full_name, self.repo.wiki_branch, self.full_path)

    @property
    def github_edit_link(self):
        return 'https://github.com/{0}/edit/{1}{2}'.format(self.repo.full_name, self.repo.wiki_branch, self.full_path)

    def get_absolute_url(self):
        return reverse('repo_detail', kwargs={'full_name': self.repo.full_name, 'path': self.full_path})

    class Meta:
        unique_together = ('repo', 'path', 'filename')
