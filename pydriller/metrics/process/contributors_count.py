"""
Module that calculates the number of developers that contributed to each
modified file in the repo in a given time range.

See https://dl.acm.org/doi/10.1145/2025113.2025119
"""
from itertools import accumulate
from pydriller import ModificationType
from pydriller.metrics.process.process_metric import ProcessMetric


class ContributorsCount(ProcessMetric):
    """
    This class is responsible to implement the following metrics:

    * Contributors Count: measures the number of contributors who modified a
      file.

    * Minor Contributors Count: measures the number of contributors who
      authored less than 5% of code of a file.
    """

    def __init__(self, path_to_repo: str,
                 since=None,
                 to=None,
                 from_commit: str = None,
                 to_commit: str = None):

        super().__init__(path_to_repo, since=since, to=to, from_commit=from_commit, to_commit=to_commit)
        self._initialize()

    def _initialize(self):

        self.contributors = {}
        self.minor_contributors = {}
        self.major_contributors = {}
        self.bus_factor = {}

        renamed_files = {}

        for commit in self.repo_miner.traverse_commits():

            for modified_file in commit.modified_files:

                filepath = renamed_files.get(modified_file.new_path,
                                             modified_file.new_path)

                if modified_file.change_type == ModificationType.RENAME:
                    renamed_files[modified_file.old_path] = filepath

                author = commit.author.email.strip()
                lines_authored = modified_file.added_lines + modified_file.deleted_lines

                self.contributors[filepath] = self.contributors.get(filepath, {})
                self.contributors[filepath][author] = self.contributors[filepath].get(author, 0) + lines_authored

        for path, contributions in list(self.contributors.items()):
            total = sum(contributions.values())
            if total == 0:
                del self.contributors[path]
            else:
                cumulative = list(accumulate(sorted(contributions.values(), reverse=True)))
                contributors_count = len(contributions.values())
                minor_contributors_count = sum(1
                                               for v in contributions.values()
                                               if v/total < .05)

                bus_factor_count = sum(1 for v in cumulative if v < total / 2)
                bus_factor_count += 1

                self.contributors[path] = contributors_count
                self.minor_contributors[path] = minor_contributors_count
                self.bus_factor[path] = bus_factor_count

    def count(self):
        """
        Return the number of contributors who modified a file.
        """
        return self.contributors

    def count_minor(self):
        """
        Return the number of contributors that authored less than
        5% of code of a file.
        """
        return self.minor_contributors

    def measure_bus_factor(self):
        """
        Return the smallest number of contributors with contributions that
        make up at least 50% of total contributions to a file.
        """
        return self.bus_factor
