@shieldsbetter/log-formatter
============================

A pleasing node log formatter with word-wrap and indentation.

```
INFO: Sometimes it's nice to get line
      wrapping with your debug output that
      respects things like:
      * Internal line breaks
      * Traditional line delimeters
      Butthatalsomaintainsindentationforde
      linquentlines
  INFO: It's also nice if recursive depth
        can be visually indicated using
        indentation without child calls
        needing to 'know' what level they
        are on.
With indentation naturally returning to
the correct depth once child calls are
complete.
      
```

Usage
-----
```javascript
var logger = require('@shieldsbetter/log-formatter');

logger.log('Output without a prefix.');
logger.log('INFO: ', 'Output with a prefix.');

logger.begin();
logger.log('Output at the next level of indentation.');

logger.begin();
logger.log('And the next!');

logger.end();
logger.end();
logger.log('Back to the bottom level.');
```

Output:

```
Output without a prefix.
INFO: Output with a prefix.
    Output at the next level of indentation.
        And the next!
Back to the bottom level.
```

Options
-------
For more fine grained control, pass options to the logger object:

```javascript
var logger = require('@shieldsbetter/log-formatter')({
            indent: 8,
            out : function(text) { process.stderr.write(text + '\n'); },
            lineLength: 78
        });
```

Your available options are:

* **indent** (default: 4) - number of spaces to indent at each level
* **out** (default: console.log) - function that processes each line of output
* **lineLength** (default: 80) - maximum column width
