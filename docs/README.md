# SPRAS Documentation

This guide explains how to work with SPRAS documentation using `sphinx` and Read
The Docs.

## Background Information

[Read The Docs](https://docs.readthedocs.com/platform/stable/), or RTD, is the
documentation hosting platform the SPRAS team has chosen to use for hosting its
official documentation. As a platform, it automatically builds and versions docs
based on the contents of the `docs/` directory in this repository by periodically
polling for changes. When a new SPRAS version is detected, Read The Docs pulls
that tag, uses it to build the relevant HTML content, and then hosts the
newly-versioned HTML content on its website as `https://spras.readthedocs.io`.

While Read the Docs is the platform that builds and hosts documentation, it is
distinct from the actual tool/package responsible for generating the HTML
content. That tool is [`sphinx`](https://www.sphinx-doc.org/en/master/), a
popular python package that tries to make documentation easy to write, structure,
and maintain.

Sphinx uses reStructured Text, or `.rst` files, to build documentation. In most
cases, your changes to the SPRAS docs will involve editing these files.

## Useful Tutorials for Working With RTD, Sphinx and reStructured Text

Before you get started working on SPRAS documentation, you might skim through
these helpful tutorials that will prime you with some basics:

- [Read The Docs Tutorial](https://docs.readthedocs.com/platform/stable/tutorial/index.html):
  This tutorial shows you how a new project could be set up with RTD, and
  highlights the steps SPRAS has already taken to connect the SPRAS repository
  with the RTD workflow. It may be useful to better understand how RTD functions
  as a platform.
- [Sphinx Tutorial](https://sphinx-tutorial.readthedocs.io/): This tutorial (and
  in general, this website) walks you through the basics of using sphinx to
  create documentation. In particular, it helps you figure out how to achieve
  the information layouts you may be after, such as certain content appearing in
  a table of contents.
- reStructured Text Resources:
  - [Getting Started with RST and Sphinx](https://sphinx-tutorial.readthedocs.io/step-1/)
    (from the Sphinx tutorial)
  - [RST Primer](https://www.sphinx-doc.org/en/master/usage/restructuredtext/basics.html#rst-primer)
  - [RST Cheatsheet](https://sphinx-tutorial.readthedocs.io/cheatsheet/)

## Editing SPRAS Documentation

The `spras` conda environment currently comes pre-bundled with the tools you
need to edit and build SPRAS's docs website, so the first step is making sure
you have an active spras environment. If you don't, refer to this repo's
[root README.md](../README.md) for instructions on installing conda and
building/activating the `spras` env.

### Building And Viewing Your Changes

It's recommended that you visualize your docs changes frequently to see what
your changes to `.rst` files look like when built by `sphinx`. Assuming you have
an activated `spras` env, you can do this by `cd`-ing into the `docs/` folder
and running:

```bash
make html
```

The output of this command will indicate whether the build was successful, and
whether there are any warnings you should consider. It's generally bad to ignore
these warnings, so if you see any, try to understand what they mean and how you
can fix them.

Once you have a successful build, the `_build` directory will contain all the
new HTML. To see visualize this content, you'll need to open files through a
browser. For example, to visit the documentation landing page, you'd visit:

```
file://<path to _build>/html/index.html
```

> **NOTE**: This filepath is formatted for Unix-like systems, and won't work on
> Windows. To adjust for Windows, use a Windows filepath.

Once you have the landing page up in your browser, you can browse the website
just like you would any other website by following links.

### Adding Changes

When you edit SPRAS docs, you'll be making changes to a combination of `.rst`
files and any python scripts used as part of the build process, such as
`docs/conf.py`. These should be committed and included in your pull request if
you want the changes to take effect. However, you should never commit the
`docs/_build` directory because Read The Docs is responsible for generating its
own build based on other `docs/` content.
