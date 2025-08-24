Maintaining SPRAS
=================

Reviewing pull requests
-----------------------

Contributors may help review pull requests from other contributors. Part
of the review process includes running the updated code locally. This
requires checking out a branch from the other contributor's fork.

We'll use pull request
`#170 <https://github.com/Reed-CompBio/spras/pull/170>`__ as an example
from the ``ntalluri`` fork with branch ``implement-eval``. First, you
need to add the ``ntalluri`` fork as a git remote from the command line
so that you can pull branches from it.

::

   git remote add ntalluri https://github.com/ntalluri/spras.git

The first ``ntalluri`` is the name we give to the new remote. It doesn't
have to match the GitHub user name, but that is a convenient convention.

Then, confirm the new remote was added

::

   git remote -v

You should see the new remote along with your ``origin`` remote and any
others you added previously. Now you can pull and fetch branches from
any of these remotes and push to any remotes where you have permissions.

To checkout the branch in the pull request locally run

::

   git fetch ntalluri
   git checkout implement-eval

Optionally run

::

   git log

To confirm that the most recent commit matches the most recent commit in
the pull request. Now your local version of SPRAS matches the code in
the pull request and you can test the code to confirm it runs as
expected.
