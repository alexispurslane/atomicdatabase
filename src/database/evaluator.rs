use lazy_regex::*;
use num_bigint::{BigInt, BigUint, Sign};

use super::{
    unification::{Constraint, Value},
    DBValue,
};

pub type VariableName = String;

pub fn char_starts_token(i: usize, c: char, sign: Sign) -> Value {
    if c.is_alphabetic() && c.is_uppercase() {
        Value::Variable(c.to_string())
    } else if c.is_alphabetic() && c.is_lowercase() {
        Value::Literal(DBValue::RelationID(c.to_string()))
    } else if c == '\"' || c == '\'' {
        Value::Literal(DBValue::Text(c.to_string()))
    } else if c.is_numeric() {
        Value::Literal(DBValue::Number(BigInt::new(sign, vec![c.to_digit(10)])))
    } else if c == '.' {
        Value::Literal(DBValue::Float(0, 0))
    } else if c == '[' {
        Value::Literal(DBValue::List(vec![]))
    } else if c == '{' {
        Value::PatternMatch {
            explicit_values: vec![],
            is_glob: false,
            glob_position: super::unification::GlobPosition::Middle,
        }
    } else {
        panic!("Unknown char `{}` at column `{}`", c, i);
    }
}

pub fn parse_line(line: String) -> Vec<Value> {
    let mut tokens = vec![];
    let mut current_token = None;
    let mut list_tokens = vec![];
    let mut digits = vec![];
    let mut sign = Sign::NoSign;

    for (i, c) in line.chars().enumerate() {
        match current_token {
            None => {
                current_token = Some(char_starts_token(i, c, sign));
            }
            Some(Value::Variable(s)) => {
                if c.is_alphanumeric() {
                    s.push(c);
                } else if c.is_whitespace() || c == ',' || c == '[' || c == '{' {
                }
            }
        }
    }
    tokens
}

pub fn parse_query(tokens: Vec<String>) -> Result<Constraint, String> {
    if let Some(alt_split_point) = tokens.iter().position(|tok| *tok == "|") {
        let (tokens_left, tokens_right) = tokens.split_at(alt_split_point);
        let (tokens_left, mut tokens_right) = (tokens_left.to_vec(), tokens_right.to_vec());
        tokens_right.remove(0);
        let parse_left = parse_query(tokens_left)?;
        let parse_right = parse_query(tokens_right)?;
        let mut left_relations = match parse_left {
            rel @ Constraint::Relation(_, _) => vec![rel],
            uni @ Constraint::Unification(_, _) => vec![uni],
            comp @ Constraint::Comparison(_, _, _) => vec![comp],
            int @ Constraint::Intersections(_) => vec![int],
            not @ Constraint::Not(_) => vec![not],
            Constraint::Alternatives(v) => v,
        };
        let right_relations = match parse_right {
            rel @ Constraint::Relation(_, _) => vec![rel],
            uni @ Constraint::Unification(_, _) => vec![uni],
            comp @ Constraint::Comparison(_, _, _) => vec![comp],
            int @ Constraint::Intersections(_) => vec![int],
            not @ Constraint::Not(_) => vec![not],
            Constraint::Alternatives(v) => v,
        };
        left_relations.extend(right_relations);
        Ok(Constraint::Alternatives(left_relations))
    } else {
        let mut parsed_tokens = vec![];
        for tok in tokens {
            let parsed_tok = parse_token(&tok)?;
            parsed_current_token = parsed_tok;
        }
        Constraint::new_relation(parsed_tokens)
    }
}

pub fn parse_fact(tokens: Vec<String>) -> Result<Vec<DBValue>, String> {
    let mut parsed_tokens = vec![];
    for tok in tokens {
        let parsed_tok = parse_token(&tok)?;
        match parsed_tok {
            Value::Literal(dbval) => { parsed_current_token = dbval },
            _ => {return Err("Cannot push variable relation as fact to database. Relations with variables can only be queries.".to_string())}
        }
    }
    Ok(parsed_tokens)
}
