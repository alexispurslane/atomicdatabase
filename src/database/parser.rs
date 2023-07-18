use num_bigint::{BigInt, BigUint, Sign, ToBigInt};

use super::{
    unification::{ASTValue, Constraint, GlobPosition},
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
    Variable(VariableName),
    PatternMatch {
        explicit_values: Vec<ASTValue>,
        is_glob: bool,
        glob_position: GlobPosition,
    },
    GreaterThan,
    EqualTo,
    LessThan,
    LessThanOrEqualTo,
    GreaterThanOrEqualTo,
    UnifyOp,
    NotOp,
    AltOp,
    IntOp,
    // lexing control ops (internal)
    NOP,
    EOL,
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

pub fn char_starts_token(i: usize, c: char, sign: Sign) -> Result<Token, String> {
    if c.is_alphabetic() && c.is_uppercase() {
        Ok(Token::Variable(c.to_string()))
    } else if c.is_alphabetic() && c.is_lowercase() {
        Ok(Token::RelationID(c.to_uppercase().to_string()))
    } else if c == '\"' || c == '\'' {
        Ok(Token::Text(String::new()))
    } else if c.is_numeric() {
        let n = BigInt::from_radix_be(sign, &vec![c.to_digit(10).unwrap() as u8], 10).unwrap();
        Ok(Token::Number(n))
    } else if c == '.' {
        Ok(Token::Float(
            BigInt::new(sign, vec![]),
            BigUint::new(vec![]),
        ))
    } else if c == '[' {
        Ok(Token::List(vec![]))
    } else if c == ']' {
        Ok(Token::EOL)
    } else if c == '{' {
        Ok(Token::PatternMatch {
            explicit_values: vec![],
            is_glob: false,
            glob_position: super::unification::GlobPosition::Middle,
        })
    } else if c == '~' {
        Ok(Token::UnifyOp)
    } else if c == '!' {
        Ok(Token::NotOp)
    } else if c == '|' {
        Ok(Token::AltOp)
    } else if c == '&' {
        Ok(Token::IntOp)
    } else if c == '<' {
        Ok(Token::LessThan)
    } else if c == '>' {
        Ok(Token::GreaterThan)
    } else if c == '=' {
        Ok(Token::EqualTo)
    } else if c.is_whitespace() {
        Ok(Token::NOP)
    } else if c == ',' {
        Ok(Token::NOP)
    } else {
        Err(format!("Unknown char `{}` at column {}", c, i))
    }
}

pub fn tokenize_line(line: String) -> Result<Vec<Token>, String> {
    let mut tokens = vec![];
    let mut current_token = None;
    let mut sign = Sign::Plus;
    let mut in_decimal = false;

    for (i, c) in (line + " ").chars().enumerate() {
        let token_end = match current_token {
            None => {
                if c == '+' {
                    sign = Sign::Plus;
                } else if c == '-' {
                    sign = Sign::Minus;
                } else {
                    if c == '.' {
                        in_decimal = true;
                    }
                    current_token = Some(char_starts_token(i, c, sign)?);
                }
                false
            }
            Some(Token::Text(ref mut s)) => {
                if c == '"' {
                    match tokens.last_mut() {
                        Some(Token::List(ref mut l)) => l.push(DBValue::Text(s.clone())),
                        _ => tokens.push(current_token.unwrap()),
                    }
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
                    let (sign, mut prevdigits) = n.to_radix_be(10);
                    prevdigits.push(c.to_digit(10).unwrap() as u8);
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
            Some(Token::List(_)) => {
                if c == ']' {
                    tokens.push(Token::NOP);
                    false
                } else {
                    tokens.push(current_token.unwrap());
                    current_token = char_starts_token(i, c, sign).ok();
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
            Some(Token::LessThan) => {
                if c == '=' {
                    current_token = Some(Token::LessThanOrEqualTo);
                    false
                } else {
                    true
                }
            }
            Some(Token::GreaterThan) => {
                if c == '=' {
                    current_token = Some(Token::GreaterThanOrEqualTo);
                    false
                } else {
                    true
                }
            }
            Some(Token::NOP) => {
                current_token = char_starts_token(i, c, sign).ok();
                false
            }
            Some(Token::EOL) => {
                tokens.push(Token::EOL);
                current_token = char_starts_token(i, c, sign).ok();
                false
            }
            _ => true,
        };
        if token_end {
            match tokens.last_mut() {
                Some(Token::List(ref mut l)) => match current_token.map(|x| x.to_dbvalue()) {
                    None => panic!("Should be unreachable"),
                    Some(Err(tok)) => {
                        return Err(format!(
                            "Unexpected operator `{:?}` in list at col {}.",
                            tok, i
                        ))
                    }
                    Some(Ok(dbval)) => l.push(dbval),
                },
                _ => tokens.push(current_token.unwrap()),
            }

            current_token = char_starts_token(i, c, sign).ok();
        }
    }
    Ok(tokens
        .into_iter()
        .filter(|x| *x != Token::NOP && *x != Token::EOL)
        .collect())
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

pub fn tokens_to_ast(tokens: Vec<Token>) -> Result<Constraint, String> {
    if let Some((left, right)) = tokens
        .iter()
        .position(|x| match x {
            Token::UnifyOp => true,
            Token::NotOp => true,
            Token::AltOp => true,
            Token::IntOp => true,
            _ => false,
        })
        .map(|i| tokens.split_at(i))
    {
        let (left_expr, op, right_expr) = (&left, &right[0], &right[1..]);

        match op {
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
                    let ast = tokens_to_ast(right_expr.to_vec())?;
                    Ok(Constraint::Not(Box::new(ast)))
                }
            }
            Token::AltOp => {
                let (left, right) = (
                    tokens_to_ast(left_expr.to_vec())?,
                    tokens_to_ast(right_expr.to_vec())?,
                );
                Ok(Constraint::Alternatives(Box::new(left), Box::new(right)))
            }
            Token::IntOp => {
                let (left, right) = (
                    tokens_to_ast(left_expr.to_vec())?,
                    tokens_to_ast(right_expr.to_vec())?,
                );
                Ok(Constraint::Intersections(Box::new(left), Box::new(right)))
            }
            _ => panic!("How could this happen? We're smarter than this!"),
        }
    } else {
        match tokens.get(1) {
            Some(Token::RelationID(r)) => Ok(Constraint::Relation(
                r.to_string(),
                tokens_to_values(&[&tokens[0..1], &tokens[2..]].concat())?,
            )),
            t => Err(format!(
                "Expected relation name in second place of plain statement, got `{:?}`",
                t
            )),
        }
    }
}

pub fn parse_line(line: String) -> Result<Constraint, String> {
    let tokens = tokenize_line(line)?;
    tokens_to_ast(tokens)
}

pub fn parse_query(lines: &str) -> Result<Vec<Constraint>, String> {
    let mut constraints = vec![];
    let mut errors = String::new();
    for (linenum, line) in lines.split(';').enumerate() {
        match parse_line(line.to_string()) {
            Ok(constraint) => constraints.push(constraint),
            Err(error_message) => {
                errors.push_str(&format!("Line {}: {}\n", linenum, error_message))
            }
        }
    }
    if errors.len() > 0 {
        Err(errors)
    } else {
        println!("{:?}", constraints);
        Ok(constraints)
    }
}

pub fn parse_fact(line: String) -> Result<Vec<DBValue>, String> {
    let tokens = tokenize_line(line)?;
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
