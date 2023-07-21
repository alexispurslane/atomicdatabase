use core::fmt;
use std::{collections::HashMap, sync::Arc};

use rand::{distributions::Alphanumeric, Rng};

use super::{parser::VariableName, DBValue};

#[derive(Clone, Debug, PartialEq)]
pub enum GlobPosition {
    Head,
    Tail,
    Middle,
}

#[derive(Clone, Debug, PartialEq)]
pub enum ASTValue {
    Literal(DBValue),
    Variable(VariableName),
    PatternMatch {
        explicit_values: Vec<ASTValue>,
        is_glob: bool,
        glob_position: GlobPosition,
    },
}

impl fmt::Display for ASTValue {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            ASTValue::Literal(val) => write!(f, "{}", val),
            ASTValue::Variable(name) => write!(f, "{}", name),
            ASTValue::PatternMatch {
                explicit_values,
                is_glob,
                glob_position,
            } => {
                // if there's no glob, the glob is nowhere, so we tell each side
                // that the glob is somewhere else!
                let glob_position = if !*is_glob {
                    &GlobPosition::Tail
                } else {
                    glob_position
                };
                match glob_position {
                    GlobPosition::Head => write!(f, "{{ .. "),
                    GlobPosition::Middle => write!(f, "{{ .. "),
                    GlobPosition::Tail => write!(f, "{{ "),
                }?;

                for val in explicit_values {
                    write!(f, "{} ", val)?;
                }

                let glob_position = if !*is_glob {
                    &GlobPosition::Head
                } else {
                    glob_position
                };
                match glob_position {
                    GlobPosition::Head => write!(f, "}}"),
                    GlobPosition::Middle => write!(f, ".. }}"),
                    GlobPosition::Tail => write!(f, ".. }}"),
                }
            }
        }
    }
}

pub fn fmt_values(av: &Vec<ASTValue>) -> String {
    av.iter().map(|x| format!("{} ", x)).collect::<String>()
}

pub fn fmt_dbvalues(av: &Vec<DBValue>) -> String {
    av.iter().map(|x| format!("{} ", x)).collect::<String>()
}

pub type RelationID = String;

pub type Bindings = HashMap<VariableName, ASTValue>;
pub fn chain_hashmap<K: Clone + Eq + std::hash::Hash, V: Clone>(
    a: HashMap<K, V>,
    b: HashMap<K, V>,
) -> HashMap<K, V> {
    a.into_iter().chain(b).collect()
}

#[derive(Debug, Clone, PartialEq, PartialOrd)]
pub enum EqOp {
    GreaterThan,
    EqualTo,
    LessThan,
    LessThanOrEqualTo,
    GreaterThanOrEqualTo,
}

impl fmt::Display for EqOp {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        use EqOp::*;
        match self {
            GreaterThan => write!(f, ">"),
            EqualTo => write!(f, "="),
            LessThan => write!(f, "<"),
            LessThanOrEqualTo => write!(f, "<="),
            GreaterThanOrEqualTo => write!(f, ">="),
        }
    }
}

pub fn unify_terms(
    i: &ASTValue,
    j: &ASTValue,
    current_bindings: &Bindings,
    environment: &Bindings,
) -> Result<Bindings, Bindings> {
    use ASTValue::*;
    match (i, j) {
        (Literal(x), Literal(y)) => {
            if x != y {
                Err(current_bindings.clone())
            } else {
                Ok(HashMap::new())
            }
        }
        (Variable(x), vy @ Literal(_)) | (vy @ Literal(_), Variable(x)) => {
            let mut safe_current_bindings = current_bindings.clone();
            safe_current_bindings.remove(x);
            if let Some(vx) = current_bindings.get(x).or(environment.get(x)) {
                let partials = lax_unify(
                    &vec![vx.clone()],
                    &vec![vy.clone()],
                    environment.clone(),
                    &safe_current_bindings,
                );
                if let Ok(binds) = partials {
                    let mut ret = HashMap::new();
                    for (k, v) in binds.into_iter() {
                        if !current_bindings.contains_key(&k) {
                            ret.insert(k, v);
                        }
                    }
                    Ok(ret)
                } else {
                    partials
                }
            } else {
                Ok(HashMap::from([(x.clone(), vy.clone())]))
            }
        }
        (xvar @ Variable(x), yvar @ Variable(y)) => {
            let x_val = current_bindings
                .get(x)
                .or(environment.get(x))
                .unwrap_or(xvar);
            let y_val = current_bindings
                .get(y)
                .or(environment.get(y))
                .unwrap_or(yvar);

            let mut safe_current_bindings = current_bindings.clone();
            safe_current_bindings.remove(x);
            safe_current_bindings.remove(y);
            if x_val == xvar && y_val == yvar {
                Ok(HashMap::from([(x.clone(), Variable(y.clone()))]))
            } else {
                let partials = lax_unify(
                    &vec![x_val.clone()],
                    &vec![y_val.clone()],
                    environment.clone(),
                    &safe_current_bindings,
                );
                if let Ok(binds) = partials {
                    let mut ret = HashMap::new();
                    for (k, v) in binds {
                        if !current_bindings.contains_key(&k) {
                            ret.insert(k, v);
                        }
                    }
                    Ok(ret)
                } else {
                    return partials;
                }
            }
        }
        (
            Literal(DBValue::List(list)),
            PatternMatch {
                explicit_values,
                is_glob,
                glob_position,
            },
        )
        | (
            PatternMatch {
                explicit_values,
                is_glob,
                glob_position,
            },
            Literal(DBValue::List(list)),
        ) => {
            let partials = unify_pattern_match(
                list,
                explicit_values,
                is_glob,
                glob_position,
                current_bindings,
            );
            if let Ok(binds) = partials {
                let mut ret = HashMap::new();
                for (k, v) in binds {
                    if !current_bindings.contains_key(&k) {
                        ret.insert(k, v);
                    }
                }
                Ok(ret)
            } else {
                return partials;
            }
        }
        _ => Err(current_bindings.clone()),
    }
}

pub fn lax_unify(
    av: &Vec<ASTValue>,
    bv: &Vec<ASTValue>,
    mut current_bindings: Bindings,
    bindings: &Bindings,
) -> Result<Bindings, Bindings> {
    for (i, j) in av.iter().zip(bv) {
        current_bindings.extend(unify_terms(i, j, &current_bindings, &bindings.clone())?);
    }
    Ok(current_bindings)
}

pub fn unify_pattern_match(
    list: &Vec<DBValue>,
    explicit_values: &Vec<ASTValue>,
    is_glob: &bool,
    glob_position: &GlobPosition,
    new_bindings: &Bindings,
) -> Result<Bindings, Bindings> {
    use ASTValue::*;
    let partials = if !is_glob {
        lax_unify(
            &explicit_values,
            &list.clone().into_iter().map(|x| Literal(x)).collect(),
            new_bindings.clone(),
            new_bindings,
        )
    } else {
        let n = explicit_values.len();
        match glob_position {
            GlobPosition::Head => lax_unify(
                &explicit_values,
                &list
                    .clone()
                    .into_iter()
                    .take(n)
                    .map(|x| Literal(x))
                    .collect(),
                new_bindings.clone(),
                new_bindings,
            ),
            GlobPosition::Tail => lax_unify(
                &explicit_values,
                &list
                    .clone()
                    .into_iter()
                    .rev()
                    .take(n)
                    .map(|x| Literal(x))
                    .collect(),
                new_bindings.clone(),
                new_bindings,
            ),
            GlobPosition::Middle => {
                // Find the complete match, or largest incomplete match, at any position in the middle of the array
                let list: Vec<ASTValue> = list.clone().into_iter().map(|x| Literal(x)).collect();
                let mut output = Err(HashMap::new());
                for i in 0..list.len() {
                    let partials = lax_unify(
                        &explicit_values,
                        &list[i..i + n].to_vec(),
                        new_bindings.clone(),
                        new_bindings,
                    );
                    if partials.is_ok() {
                        output = partials;
                    } else if output.is_err() {
                        let len1 = partials.as_ref().map_err(|x| x.len()).unwrap_err();
                        let len2 = output.as_ref().map_err(|x| x.len()).unwrap_err();
                        if len1 > len2 {
                            output = partials;
                        }
                    }
                }
                output
            }
        }
    };
    partials
}

pub fn unify_compare(op: &EqOp, a: &ASTValue, b: &ASTValue, bindings: Arc<Bindings>) -> bool {
    use ASTValue::*;
    match (a, b) {
        (Literal(a), Literal(b)) => match op {
            EqOp::GreaterThan => a > b,
            EqOp::EqualTo => a == b,
            EqOp::LessThan => a < b,
            EqOp::LessThanOrEqualTo => a <= b,
            EqOp::GreaterThanOrEqualTo => a >= b,
        },
        (Variable(x), b @ Literal(_)) => {
            if let Some(xval) = bindings.get(x) {
                unify_compare(op, xval, b, bindings.clone())
            } else {
                true
            }
        }
        (a @ Literal(_), Variable(y)) => {
            if let Some(yval) = bindings.get(y) {
                unify_compare(op, a, yval, bindings.clone())
            } else {
                true
            }
        }
        (Variable(x), Variable(y)) => match (bindings.get(x), bindings.get(y)) {
            (Some(xval), Some(yval)) => unify_compare(op, xval, yval, bindings.clone()),
            (None, Some(_)) => true,
            (Some(_), None) => true,
            (None, None) => true,
        },
        _ => false,
    }
}

pub fn fmt_ptr_bindings(b: &Bindings) -> String {
    let mut s = String::new();
    s.push_str("{ ");
    let mut keyvals = b.iter().collect::<Vec<(_, _)>>();
    keyvals.sort_by(|(k1, _), (k2, _)| k1.cmp(k2));
    for (k, v) in keyvals {
        s.push_str(&format!("{} ~ {}, ", k, v));
    }
    s.push_str("}");
    s
}

pub fn unify_get_variable_value(
    varname: &String,
    current_bindings: &Bindings,
    environment: &Bindings,
) -> Option<ASTValue> {
    let get_name = format!(
        "GETVALUE#{}",
        rand::thread_rng()
            .sample_iter(&Alphanumeric)
            .take(3)
            .map(char::from)
            .collect::<String>(),
    );
    let lvalue = vec![ASTValue::Variable(get_name.clone())];
    let rvalue = vec![ASTValue::Variable(varname.clone())];
    lax_unify(&lvalue, &rvalue, current_bindings.clone(), &environment)
        .ok()
        .expect(&format!("Cannot unify {} with a variable?!", rvalue[0]))
        .get(&get_name)
        .map(|x| x.clone())
}

pub fn fmt_arc_bindings(b: Arc<Bindings>) -> String {
    fmt_ptr_bindings(b.as_ref())
}
