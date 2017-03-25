# Backend

## layer one

1. Listen for JSON queries from the database (including facts and queries)
2. Listen for NL query-equations for inferences from the front end
5. Send inferences or data back in JSON.

## layer two

1. Queries will be able to be formatted as NL in addition.
2. Disallow redefinition of query-equations.

# Front end

## layer one

1. Have massive table interface (similar to excel) that can be
converted into JSON AEV-triples
2. Have a text-box for entering query equations. When the user hits enter or clicks the 'Compute' button, send message to server.
3. Unknowns in the table (parenthisized words) should be, when solved,
changed into their correct answer.
4. Solve button on the bottom of the screen.
5. When table cell is double-clicked, change cell contents to a textbox with the originoal text of the cell.
6. When user clicks out of cell after double-clicking it, change the cell back to regular text with the contents of the textbox. Send the server a message with the changes.


# AEV cheatsheat

- [A]ttribute - the property in JavaScript parlance.
- [E]ntity - the object in JavaScript parlance.
- [V]alue - the value in JavaScript parlance.

The attribute corrisponds to the column, the entity corrisponds to the row, the value to the cell at the intersection of row and col (or entity and attribute).

The following table:

00   | name | age
--------|------|----
person1 | Joe  | 12
person2 | Tom  | 22

would be stored in these AEV triples:

```
[name, person1, Joe]
[age,  person1,  12]

[name, person2, Tom]
[age,  person2,  22]
```

and would be equivilant to:

```
person1.name = "Joe";
person1.age  = 12;

person2.name = "Tom";
person2.age  = 22;
```
