use lazy_regex::*;
use num_bigint::{BigInt, BigUint, Sign};

use super::{
    unification::{Constraint, Value},
    DBValue,
};

pub type VariableName = String;

pub fn tokenize(line: String) -> Vec<String> {
    line.split_whitespace()
        .map(|s| s.to_owned())
        .collect::<Vec<String>>()
}

pub fn parse_token(tok: &str) -> Result<Value, String> {
    let text = regex_captures!(r#"\"([^\"]*)\""#, tok);
    let number = regex_captures!(r#"(\+|\-)?(\d+)"#, tok);
    let float = regex_captures!(r#"(\+|\-)?(\d*)\.(\d)"#, tok);
    let variable = regex_captures!(r#"([A-Z][a-zA-Z0-9_]*)"#, tok);
    let relation = regex_captures!(r#"(\w+)"#, tok);
    if let Some((_, string)) = text {
        Ok(Value::Literal(DBValue::Text(string.to_string())))
    } else if let Some((_, sign, digits)) = number {
        let sign = match sign {
            "+" => Sign::Plus,
            "-" => Sign::Minus,
            _ => Sign::NoSign,
        };
        Ok(Value::Literal(DBValue::Number(BigInt::new(
            sign,
            digits.chars().filter_map(|c| c.to_digit(10)).collect(),
        ))))
    } else if let Some((_, sign, digits, decimals)) = float {
        let sign = match sign {
            "+" => Sign::Plus,
            "-" => Sign::Minus,
            _ => Sign::NoSign,
        };
        Ok(Value::Literal(DBValue::Float(
            BigInt::new(
                sign,
                digits.chars().filter_map(|c| c.to_digit(10)).collect(),
            ),
            BigUint::new(decimals.chars().filter_map(|c| c.to_digit(10)).collect()),
        )))
    } else if let Some((_, varname)) = variable {
        Ok(Value::Variable(varname.to_string()))
    } else if let Some((_, relID)) = relation {
        Ok(Value::Literal(DBValue::RelationID(relID.to_uppercase())))
    } else {
        Err(format!("Cannot parse token: `{}`", tok))
    }
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
            parsed_tokens.push(parsed_tok);
        }
        Constraint::new_relation(parsed_tokens)
    }
}

pub fn parse_fact(tokens: Vec<String>) -> Result<Vec<DBValue>, String> {
    let mut parsed_tokens = vec![];
    for tok in tokens {
        let parsed_tok = parse_token(&tok)?;
        match parsed_tok {
            Value::Literal(dbval) => { parsed_tokens.push(dbval) },
            _ => {return Err("Cannot push variable relation as fact to database. Relations with variables can only be queries.".to_string())}
        }
    }
    Ok(parsed_tokens)
}
