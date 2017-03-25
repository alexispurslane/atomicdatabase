linewrap
========

A fork of [wordwrap](https://github.com/substack/node-wordwrap) that's faster and more powerful,
supporting HTML, ANSI Color Codes, multiple paragraphing styles, and more.

On a 3.4GHz Sandy Bridge core, Linewrap achieves roughly 20MB/s when wrapping
at 80 columns, or 15MB/s if wrapping at 20 columns.

Linewrap is *almost* backwards compatible with wordwrap. The behavior only differs
in some edge cases where I believe wordwrap didn't make the best choice. You probably
won't notice any difference in normal usage.

Install
=======

    npm install linewrap

Usage
=====

```js
    var linewrap = require('linewrap');

    // Wrap the string at 20 columns, using Windows-style line breaks.
    var wrap = linewrap(20, {lineBreak: '\r\n' /*, other options */});
    console.log(wrap('You and your whole family are made out of meat.'));

    // Wrap the string at 20 columns, prepend 10 spaces to each line, and
    // skip HTML tags when counting columns for wrapping.
    var wrap = linewrap(10, 30, {skipScheme: 'html' /*, other options */});
    console.log(wrap('You and your <b>whole family</b> are made out of <i>meat</i>.'));
```


Options
=======

Skip strings
------------

**Relevant options**: `skip`, `skipScheme`.

Sometimes certain characters in the text are used to control styling, annotate
additional information, etc, and are not intended to be displayed. Examples
include HTML tags and ANSI color codes. These characters shouldn't be counted
when doing a wrap.

**Supported values** of `skip`:

1. `RegExp`.
2. `string`.

The specified regular expression or string is matched against the input, and all
matching sequences in the input are simply copied to the output and are ignored
by the wrapping algorithm.

`skipScheme` can take one of the following values: `"ansi-color"`, `"html"`, and
`"bbcode"`. They are pre-configured regular expressions for common tasks.

When both options are specified, `skip` takes precedence.


Line break strings
------------------

**Relevant options**: `lineBreak`, `lineBreakScheme`.

To support custom line breaks, there are actually two parameters that need to be
specified: a regular expression that is used to match line breaks in the input (`P1`),
and a string that is used as line breaks in the output (`P2`).

**Supported values** of `lineBreak`:

1. `string`. It is used as `P2`, and a `RegExp` object is created from the string
   to be used as `P1`.
2. `[RegExp, string]`. The `RegExp` object is used as `P1`, and the string is used
   as `P2`.
3. `[string, string]`. A `RegExp` object is created from the first string and used
   as `P1`, the second string is used as `P2`.
4. `RegExp`. It is used as `P1`. We will match the regular expression against the
   input and use the first match as `P2`. If no match is found, an exception is
   thrown. **Not Recommended**

You can, for example, use `/\n/` as `P1` and `"<br>"` as `P2` to convert the string
from one format to another.

`lineBreakScheme` can take one of the following values: `"unix"`, `"dos"`, `"mac"`,
`"html"`, and `"xhtml"`. Each scheme specifies both `P1` and `P2` for the specific
scenario.

When both options are specified, `lineBreak` takes precedence.


Existing line breaks
--------------------

**Relevant option**: `respectLineBreaks`.

This option controls how to treat existing line breaks in the input. It's important
for supporting various paragraphing styles.

**Supported values**:

1. `"all"` **Default**. All existing line breaks are preserved.
2. `"none"`. All existing line breaks are discarded.
3. `"multi"`. Only 2 or more consecutive line breaks (there can be whitespaces
   between them) are preserved, single line breaks are discarded. This can be
   used to support the paragraphing style that inserts a blank line between
   paragraphs, so that each paragraph is re-formatted, but the paragraph structure
   is preserved.
4. `"m<num>"`. A number is specified to indicate how many consecutive line breaks
   are preserved. For example, `"multi"` is equivalent to `"m2"`.
5. `"s<num>"`. A number is specified to indicate line breaks that are immediately
   followed by at least how many whitespaces are preserved. This can be used to
   support the paragraphing style that indents the first line of each paragraph.


Whitespaces
-----------

**Relevant option**: `whitespace`.

This option controls whether preceding and trailing whitespaces are stripped from
the output. The original wordwrap isn't consistent in this area: it strips preceding
whitespaces of all lines except the first one, and it strips trailing whitespaces of
some lines but not others.

**Supported values**:

1. `"default"` **Default**. Both preceding and trailing whitespaces are stripped.
   This is the most similar to wordwrap's behavior.
2. `"collapse"`. In addition to `"default"`, also collapse consecutive whitespaces
   within each line.
3. `"line"`. Similar to `"default"`, but doesn't strip preceding whitespaces of
   lines preserved from the input (not wrapped by us). This option can be used
   with the `"s<num>"` options of `respectLineBreaks` to support the indenting
   paragraphing style, so that the indentations to mark new paragraphs are preserved.
   Preceding whitespaces are also significant in markup languages like Markdown.
4. `"all"`. All whitespaces are preserved. In this mode, whitespaces are treated
   like other non-alphabetical characters that are displayed but can be wrapped
   at any position.


Additional indentation in preserved lines
----------------------------------------

**Relevant option**: `preservedLineIndent`.

This option applies additional indentation to lines preserved from the input. This
can be used, for example, to convert from the blank-line paragraphing style to the
indenting paragraphing style.

`preservedLineIndent` must be a non-negative integer specifying the amount of the
indentation. If specified, all preserved lines will be indented by this amount.


Additional indentation in wrapped lines
----------------------------------------

**Relevant option**: `wrapLineIndent`, `wrapLineIndentBase`.

This option applies additional indentation to wrapped lines. This allows fine control
over the alignment of wrapped text, illustrated in the following example:

    Red: the color of blood, rubies
         and strawberries.
    Green: the color of growing grass
           and leaves, of emeralds,
           and of jade.
    Blue: the color of the clear sky
          and the deep sea.

**Supported values** of `wrapLineIndentBase`:

1. `RegExp`.
2. `string`.

`wrapLineIndent` must be an integer specifying the amount of the indentation. If only
`wrapLineIndent` is specified, it must be a non-negative integer, and all wrapped lines
are indented by this amount. If `wrapLineIndentBase` is also specified, it's searched
in each preserved line: if found, all wrapped lines belonging to this preserved line
are indented by the sum of `wrapLineIndent` and the index of the match (if the sum is
a positive integer); if not found, the wrapped lines belonging to this preserved line
are not indented.

For example, `wrapLineIndentBase: ':', wrapLineIndent: 2` can be used to generate the
result in the above example.


Hard wrapping
-------------

**Relevant option**: `mode`.

**Supported values**:

1. `"soft"` **Default**. Split chunks by `/(\S+\s+/` and don't break up chunks which are
   longer than the wrap length. So if a single word is longer than the wrap
   length it will overflow.
2. `"hard"`. Split chunks with `/\b/` and break up chunks longer than the wrap
   length.


Tab width
---------

**Relevant option**: `tabWidth`.

All `\t` characters are replaced with a certain number of spaces before doing
the wrap. This option controls how many spaces to replace a `\t`. Default is 4.


Presets
-------

**Relevant option**: `preset`.

Are you overwhelmed by the sheer amount of options? Worry not, presets are to
the rescue!

Each preset contains values for one or more options. You can specify either a
single preset or an array of presets. If multiple presets in the array set the
same option, the last one wins.

**Supported values**:

1. `"html"`. Sets `skipScheme` and `lineBreakScheme` to `"html"`, and `whitespace`
   to `"collapse"`.

Options that are set explicitly take predence to those set by a preset.

You are welcome to suggest new schemes and presets by
[creating an issue](https://github.com/halfninety/node-linewrap/issues/new).


Acknowledgements
================

Thanks to [James Halliday](https://github.com/substack) for wordwrap.


License
=======

MIT License
