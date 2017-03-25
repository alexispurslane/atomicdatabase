# Backend

## layer one

1. Listen for JSON queries from the database (including facts and queries)
2. Listen for NL query-equations for inferences from the front end
3. Send inferences or data back in JSON.

## layer two

1. Queries will be able to be formatted as NL in addition.
2. Disallow redefinition of query-equations.

# Front end

## layer one

1. Have massive table interface (similar to excel) that can be converted into JSON AEV-triples
2. Have a text-box for entering query equations.
3. Unknowns in the table (parenthisized words) should be, when solved, changed into their correct answer.
4. Solve button on the bottom of the screen.
