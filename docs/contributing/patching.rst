Patching Algorithms
===================

Some wrapped algorithms require extra fixes inside their code. For permissively licensed algorithms,
we use ``.patch`` files generated from ``git format-patch``.

To create patch files using ``git format-patch`` (assuming your wrapped algorithm is in a git repository):

#. Clone the repository locally.
#. Commit the changes you want to make (with good commit messages and descriptions).

    * Distinct changes should be made in different commits to make patch files easy to read
    * For removing code, we prefer to comment out code instead of removing it, to make potential stacktraces less confusing for end users.

#. Run ``git format-patch HEAD~[N]`` where ``N`` is the number of commits you made.

To use ``.patch`` files in ``Dockerfiles``, we create a fake user for ``git`` and apply the patch files using ``git am``:

.. code:: shell

    git config user.email "email@example.com"
    git config user.name "Non-existent User"
    git am /0001-my-patch.patch
