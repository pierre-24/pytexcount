# `pytexcount`

Count the number of words in a TeX document, but tries to be clever about it.

## Install & usage

```bash
pip install --upgrade git+https://github.com/pierre-24/pytexcount.git
```

No dependencies are required (except python, of course).

Usage:

```text
$ pytexcount test.tex
23
```

## More information

The program parses the TeX document to extract an AST (in order to count only when necessary).

By default, the count included all environment (except a few, like equations)
but exclude all macro (except a few, like title levels and formating).
You can have an overview with the `-s` option:

```text
$  pytexcount -s
Excluded env: equation, equation*, align, align*
Included macros: textbf, textit, texttt, emph, caption, section, subsection, subsubsection, paragraph, subparagraph
```

You can add macro to the list with the `-i` option (using a colon-separated list), and exclude additional environment with the `-e` option.

For example, to include `\ref{}` and `\cite{}` but exclude the `abstract` environment,

```text
$ pytexcount test.tex -i ref,cite -e abstract
43
```

## Contributions

Contribution, either with [issues](https://github.com/pierre-24/pytexcount/issues) or [pull requests](https://github.com/pierre-24/pytexcount/pulls) are welcomed.

If you can to contribute, this is the usual deal: 
start by [forking](https://guides.github.com/activities/forking/), then clone your fork

```bash
git clone git@github.com:<YOUR_USERNAME>/pytexcount.git
cd pytexcount
```

Then setup... And you are good to go :)

```bash
python -m venv venv # a virtualenv is always a good idea
source venv/bin/activate
make init  # install what's needed for 
```

Don't forget to work on a separate branch, and to run the linting and tests:

```bash
make lint  # flake8
make test  # unit tests
```

