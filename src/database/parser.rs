use num_bigint::{BigInt, BigUint, Sign, ToBigInt};

use super::{
    unification::{ASTValue, Constraint, EqOp, GlobPosition},
    DBValue,
};

pub type VariableName = String;

#[derive(Clone, Debug, PartialEq)]
pub enum Token {
    Text(String),
    Number(BigInt),
    Float(BigInt, BigUint),
    RelationID(String),
    List(Vec<DBValue>),
    Group(Vec<Token>),
    Variable(VariableName),
    PatternMatch {
        explicit_values: Vec<ASTValue>,
        is_glob: bool,
        glob_position: GlobPosition,
    },
    RuleOp,
    UnifyOp,
    EqOp(EqOp),
    NotOp,
    AltOp,
    IntOp,
    // lexing control ops (internal)
    IntermediateList(String),
    IntermediateGroup(String),
    NOP,
    StatementEnd,
}

pub trait ToASTValue {
    fn to_value(self) -> Result<ASTValue, Token>;
}

impl ToASTValue for Token {
    fn to_value(self) -> Result<ASTValue, Token> {
        use Token::*;
        match self.to_dbvalue() {
            Ok(dbval) => Ok(ASTValue::Literal(dbval)),
            Err(Variable(var)) => Ok(ASTValue::Variable(var)),
            Err(PatternMatch {
                explicit_values,
                is_glob,
                glob_position,
            }) => Ok(ASTValue::PatternMatch {
                explicit_values,
                is_glob,
                glob_position,
            }),
            Err(tok) => Err(tok),
        }
    }
}

pub trait ToDBValue {
    fn to_dbvalue(self) -> Result<DBValue, Token>;
}

impl ToDBValue for Token {
    fn to_dbvalue(self) -> Result<DBValue, Token> {
        use Token::*;
        match self {
            Text(a) => Ok(DBValue::Text(a)),
            Number(a) => Ok(DBValue::Number(a)),
            Float(a, b) => Ok(DBValue::Float(a, b)),
            RelationID(a) => Ok(DBValue::RelationID(a)),
            List(a) => Ok(DBValue::List(a)),
            _ => Err(self),
        }
    }
}

impl ToDBValue for String {
    fn to_dbvalue(self) -> Result<DBValue, Token> {
        Ok(DBValue::Text(self))
    }
}

impl ToDBValue for isize {
    fn to_dbvalue(self) -> Result<DBValue, Token> {
        let bigint = self.to_bigint().ok_or(Token::NOP)?;
        Ok(DBValue::Number(bigint))
    }
}

impl ToDBValue for usize {
    fn to_dbvalue(self) -> Result<DBValue, Token> {
        let bigint = self.to_bigint().ok_or(Token::NOP)?;
        Ok(DBValue::Number(bigint))
    }
}

impl ToDBValue for f64 {
    fn to_dbvalue(self) -> Result<DBValue, Token> {
        let tokens = tokenize_line(format!("{}", self)).ok().ok_or(Token::NOP)?;
        let float = tokens.get(0).ok_or(Token::NOP)?;
        (float.clone()).to_dbvalue()
    }
}

pub fn char_starts_token(i: usize, c: char) -> Result<Token, String> {
    match c {
        '\"' | '\'' => Ok(Token::Text(String::new())),
        '.' => Ok(Token::StatementEnd),
        '[' => Ok(Token::IntermediateList(String::new())),
        '(' => Ok(Token::IntermediateGroup(String::new())),
        '{' => Ok(Token::PatternMatch {
            explicit_values: vec![],
            is_glob: false,
            glob_position: super::unification::GlobPosition::Middle,
        }),
        '~' => Ok(Token::UnifyOp),
        '!' => Ok(Token::NotOp),
        ';' => Ok(Token::AltOp),
        ',' => Ok(Token::IntOp),
        ':' => Ok(Token::RuleOp),
        '<' => Ok(Token::EqOp(EqOp::LessThan)),
        '>' => Ok(Token::EqOp(EqOp::GreaterThan)),
        '=' => Ok(Token::EqOp(EqOp::EqualTo)),
        // for the next two: we need to start a number that has no digits, but
        // obviously that's nonsensical, so we need to put some digit in there,
        // but a digit we can distinguish from one that was put in there by a
        // branch that starts the number with a digit instead of no digits, so
        // we can know to remove it, since it's arbitrary garbage. To do this,
        // we take advantage of the fact that BigInt/BigUint can have arbitrary
        // radices, but this language only uses base ten, to put in a digit with
        // an absurdly high value that you'd never get in a single digit of a
        // base ten system, so we know that this is a control digit that can be
        // discarded
        '+' => Ok(Token::Number(
            BigInt::from_radix_be(Sign::Plus, &vec![255], 256).unwrap(),
        )),
        '-' => Ok(Token::Number(
            BigInt::from_radix_be(Sign::Minus, &vec![255], 256).unwrap(),
        )),

        c if c.is_whitespace() => Ok(Token::NOP),
        c if c.is_alphabetic() && c.is_uppercase() => Ok(Token::Variable(c.to_string())),
        c if c.is_alphabetic() && c.is_lowercase() => {
            Ok(Token::RelationID(c.to_uppercase().to_string()))
        }
        c if c.is_numeric() => Ok(Token::Number(
            BigInt::from_radix_be(Sign::Plus, &vec![c.to_digit(10).unwrap() as u8], 10).unwrap(),
        )),

        _ => Err(format!("Unknown char `{}` at column {}", c, i)),
    }
}

pub fn tokenize_line(line: String) -> Result<Vec<Token>, String> {
    let mut tokens = vec![];
    let mut current_token = None;
    let mut in_decimal = false;
    let mut list_depth = 0;
    let mut paren_depth = 0;

    for (i, c) in (line + " ").chars().enumerate() {
        if c == '[' {
            list_depth += 1;
        }
        if c == '(' {
            paren_depth += 1;
        }
        let token_end = match current_token {
            None => {
                if c == '.' {
                    in_decimal = true;
                }
                current_token = Some(char_starts_token(i, c)?);
                false
            }
            Some(Token::Text(ref mut s)) => {
                if c == '"' {
                    tokens.push(current_token.unwrap());
                    current_token = None;
                    false
                } else {
                    s.push(c);
                    false
                }
            }
            Some(Token::RelationID(ref mut s)) => {
                if c.is_alphanumeric() {
                    s.push(c.to_uppercase().collect::<Vec<char>>()[0]);
                    false
                } else {
                    true
                }
            }
            Some(Token::Number(ref mut n)) => {
                if c.is_numeric() {
                    let digit = c.to_digit(10).unwrap() as u8;
                    // get sign and digits at test-radix, so we can see our test
                    // value
                    let (sign, mut prevdigits) = n.to_radix_be(256);
                    // test value is here, we don't need the previous digits and
                    // can start over with this digit
                    if prevdigits[0] == 255 {
                        prevdigits = vec![digit]
                    } else {
                        // otherwise, we really wanted digits in base 10, so ask
                        // for that, then add our new digit
                        prevdigits = n.to_radix_be(10).1;
                        prevdigits.push(digit);
                    }
                    *n = BigInt::from_radix_be(sign, &prevdigits, 10).unwrap();
                    false
                } else if c == '.' {
                    in_decimal = true;
                    current_token = Some(Token::Float(n.clone(), BigUint::new(vec![])));
                    false
                } else {
                    true
                }
            }
            Some(Token::IntermediateGroup(ref mut s)) => {
                if c == ')' {
                    paren_depth -= 1;
                    if paren_depth == 0 {
                        tokens.push(Token::Group(tokenize_line(s.to_string())?));
                        current_token = None;
                    } else {
                        s.push(c);
                    }
                    false
                } else {
                    s.push(c);
                    false
                }
            }
            Some(Token::IntermediateList(ref mut s)) => {
                if c == ']' {
                    list_depth -= 1;
                    if list_depth == 0 {
                        tokens.push(Token::List(tokens_to_dbvalues(tokenize_line(
                            s.to_string(),
                        )?)?));
                        current_token = None;
                    } else {
                        s.push(c);
                    }
                    false
                } else {
                    s.push(c);
                    false
                }
            }
            Some(Token::Float(ref mut a, ref mut b)) => {
                if c.is_numeric() {
                    if in_decimal {
                        let mut prevdigits = b.to_radix_be(10);
                        prevdigits.push(c.to_digit(10).unwrap() as u8);
                        *b = BigUint::from_radix_be(&prevdigits, 10).unwrap();
                    } else {
                        let (sign, mut prevdigits) = a.to_radix_be(10);
                        prevdigits.push(c.to_digit(10).unwrap() as u8);
                        *a = BigInt::from_radix_be(sign, &prevdigits, 10).unwrap();
                    }
                    false
                } else {
                    true
                }
            }

            Some(Token::PatternMatch { .. }) => {
                return Err(format!(
                    "Met character `{}` in unimplemented token PatternMatch",
                    c
                ))
            }
            Some(Token::Variable(ref mut s)) => {
                if c.is_alphanumeric() {
                    s.push(c);
                    false
                } else {
                    true
                }
            }
            Some(Token::EqOp(EqOp::LessThan)) => {
                if c == '=' {
                    current_token = Some(Token::EqOp(EqOp::LessThanOrEqualTo));
                    false
                } else {
                    true
                }
            }
            Some(Token::EqOp(EqOp::GreaterThan)) => {
                if c == '=' {
                    current_token = Some(Token::EqOp(EqOp::GreaterThanOrEqualTo));
                    false
                } else {
                    true
                }
            }
            Some(Token::NOP) => {
                current_token = char_starts_token(i, c).ok();
                false
            }
            _ => true,
        };
        if token_end {
            tokens.push(current_token.unwrap());
            current_token = char_starts_token(i, c).ok();
        }
    }
    Ok(tokens.into_iter().filter(|x| *x != Token::NOP).collect())
}

pub fn tokens_to_values(tokens: &[Token]) -> Result<Vec<ASTValue>, String> {
    tokens
        .iter()
        .map(|x| x.clone().to_value())
        .try_fold(vec![], |acc, x| {
            if let Ok(x) = x {
                Ok([acc, vec![x]].concat())
            } else {
                Err(format!("Unexpected value: `{:?}`", x))
            }
        })
}

pub fn tokens_to_dbvalues(tokens: Vec<Token>) -> Result<Vec<DBValue>, String> {
    let mut dbvalues = vec![];
    for tok in tokens {
        dbvalues.push(match tok {
            Token::Text(a) => DBValue::Text(a),
            Token::Number(a) => DBValue::Number(a),
            Token::Float(a, b) => DBValue::Float(a, b),
            Token::RelationID(a) => DBValue::RelationID(a),
            Token::List(a) => DBValue::List(a),
            t => return Err(format!("Invalid token {:?} in fact", t)),
        });
    }
    Ok(dbvalues)
}

macro_rules! precidence_table {
    ($tokens: ident, $( $p:pat ),+) => {
        vec![$( $tokens.iter().position(|x| match x {
            $p => true,
            _ => false
        }) ),+].iter().fold(None, |x, y| x.or(*y))
    };
}

pub fn tokens_to_constraint(tokens: Vec<Token>) -> Result<Constraint, String> {
    // split at lowest precidence operators first

    if let Some((left, right)) = precidence_table!(
        tokens,
        Token::AltOp,
        Token::IntOp,
        Token::UnifyOp,
        Token::NotOp,
        Token::EqOp(_)
    )
    .map(|i| tokens.split_at(i))
    {
        let (left_expr, op, right_expr) = (&left, &right[0], &right[1..]);

        match op {
            Token::AltOp => {
                let (left, right) = (
                    tokens_to_constraint(left_expr.to_vec())?,
                    tokens_to_constraint(right_expr.to_vec())?,
                );
                let (left_vec, right_vec) = (
                    if let Constraint::Alternatives(av) = left {
                        av
                    } else {
                        vec![left]
                    },
                    if let Constraint::Alternatives(av) = right {
                        av
                    } else {
                        vec![right]
                    },
                );
                Ok(Constraint::Alternatives(
                    vec![left_vec, right_vec].into_iter().flatten().collect(),
                ))
            }
            Token::IntOp => {
                let (left, right) = (
                    tokens_to_constraint(left_expr.to_vec())?,
                    tokens_to_constraint(right_expr.to_vec())?,
                );
                let (left_vec, right_vec) = (
                    if let Constraint::Intersections(av) = left {
                        av
                    } else {
                        vec![left]
                    },
                    if let Constraint::Intersections(av) = right {
                        av
                    } else {
                        vec![right]
                    },
                );
                Ok(Constraint::Intersections(
                    vec![left_vec, right_vec].into_iter().flatten().collect(),
                ))
            }
            Token::UnifyOp => {
                let (left, right) = (tokens_to_values(left_expr)?, tokens_to_values(right_expr)?);
                Ok(Constraint::Unification(left, right))
            }
            Token::NotOp => {
                if left_expr.len() > 0 {
                    Err(
                        "Cannot have a negation not at the beginning of an expression! "
                            .to_string(),
                    )
                } else if right_expr.len() == 0 {
                    Err("An expression must follow a not operator. ".to_string())
                } else {
                    let ast = tokens_to_constraint(right_expr.to_vec())?;
                    Ok(Constraint::Not(Box::new(ast)))
                }
            }
            Token::EqOp(op) => {
                let (mut left, mut right) =
                    (tokens_to_values(left_expr)?, tokens_to_values(right_expr)?);
                if left.len() != 1 || right.len() != 1 {
                    Err("Cannot have more than one value on either end of a comparison".to_string())
                } else {
                    Ok(Constraint::Comparison(
                        op.clone(),
                        left.remove(0),
                        right.remove(0),
                    ))
                }
            }
            _ => panic!("How could this happen? We're smarter than this!"),
        }
    } else {
        if let Some(Token::RelationID(r)) = tokens.get(1) {
            Ok(Constraint::Relation(
                r.to_string(),
                tokens_to_values(&[&tokens[0..1], &tokens[2..]].concat())?,
            ))
        } else if let Some(Token::Group(group)) = tokens.get(0) {
            println!("{:?}", tokens);
            if tokens.len() == 1 {
                tokens_to_constraint(group.to_vec())
            } else {
                Err(format!("Cannot put two group expressions next to each other without some kind of operator determining how they'll be evaluated together"))
            }
        } else {
            Err(format!(
                "Expected valid expression (relation or group), got {:?}",
                tokens
            ))
        }
    }
}

pub fn parse_line(line: String) -> Result<Constraint, String> {
    let tokens = tokenize_line(line)?;
    tokens_to_constraint(tokens)
}

pub fn parse_fact(line: String) -> Result<Vec<DBValue>, String> {
    let tokens = tokenize_line(line)?;
    tokens_to_dbvalues(tokens)
}

pub enum MetaAST {
    Constraint(Constraint),
    Rule(Vec<ASTValue>, Vec<Constraint>),
    Fact(Vec<DBValue>),
}

pub fn parse_file(lines: String) -> Result<Vec<MetaAST>, String> {
    let mut statements = vec![];
    let mut statement = vec![];
    let tokens = tokenize_line(lines.to_string())?;
    for tok in tokens {
        if tok == Token::StatementEnd {
            if statement.len() > 0 {
                statements.push(statement);
                statement = vec![];
            }
        } else {
            statement.push(tok);
        }
    }

    let mut constraints = vec![];
    for (linenum, tokens) in statements.into_iter().enumerate() {
        if let Ok(fact) = tokens_to_dbvalues(tokens.clone()) {
            constraints.push(MetaAST::Fact(fact));
        } else {
            if let Some((left, right)) = tokens
                .iter()
                .position(|x| *x == Token::RuleOp)
                .map(|i| tokens.split_at(i))
            {
                let (signature, _, body) = (&left, &right[0], &right[1..]);
                let signature = tokens_to_values(signature).map_err(|x| {
                    format!(
                        "Line {}: Unexpected error '{}' in rule signature.",
                        linenum, x
                    )
                })?;
                if signature
                    .get(1)
                    .and_then(|name| {
                        if let ASTValue::Literal(DBValue::RelationID(_)) = name {
                            Some(name)
                        } else {
                            None
                        }
                    })
                    .is_none()
                {
                    return Err(format!(
                        "Line {}: Need at least one relation-id keyword in rule signature. ",
                        linenum
                    ));
                }
                let body = {
                    let constraint = tokens_to_constraint(body.to_vec()).map_err(|x| {
                        format!("Line {}: Unexpected error '{}' in rule body.", linenum, x)
                    })?;
                    if let Constraint::Intersections(b) = constraint {
                        b
                    } else {
                        vec![constraint]
                    }
                };

                constraints.push(MetaAST::Rule(signature, body));
            } else {
                let constraint = tokens_to_constraint(tokens).map_err(|x| {
                    format!("Line {}: Unexpected error '{}' in constraint.", linenum, x)
                })?;
                constraints.push(MetaAST::Constraint(constraint))
            }
        }
    }
    Ok(constraints)
}
