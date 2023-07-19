use core::fmt;
use std::{
    collections::HashMap,
    iter::{empty, FlatMap},
    sync::Arc,
};

use crate::database::backtracking::BacktrackingQuery;

use super::{parser::VariableName, DBValue, Database};

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

#[derive(Debug, Clone, PartialEq)]
pub enum Constraint {
    Relation(RelationID, Vec<ASTValue>),
    Unification(Vec<ASTValue>, Vec<ASTValue>),
    Comparison(EqOp, ASTValue, ASTValue),
    Not(Box<Constraint>),
    Alternatives(Vec<Constraint>),
    Intersections(Vec<Constraint>),
}

impl fmt::Display for Constraint {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        use Constraint::*;
        match self {
            Relation(rel, values) => {
                write!(f, " {} {}", rel, values[0])?;
                for val in values.iter().skip(1) {
                    write!(f, " {}", val)?;
                }
                fmt::Result::Ok(())
            }
            Unification(av, bv) => {
                for val in av.iter() {
                    write!(f, "{} ", val)?;
                }
                write!(f, "~ ")?;
                for val in bv.iter() {
                    write!(f, "{} ", val)?;
                }
                fmt::Result::Ok(())
            }
            Comparison(op, a, b) => write!(f, "{} {} {}", a, op, b),
            Not(constraint) => write!(f, "!{}", constraint),
            Alternatives(av) => {
                write!(f, "( ")?;
                for (i, constraint) in av.iter().enumerate() {
                    if i == av.len() - 1 {
                        write!(f, "{}", constraint)?;
                    } else {
                        write!(f, "{};", constraint)?;
                    }
                }
                write!(f, " )")
            }
            Intersections(av) => {
                write!(f, "( ")?;
                for (i, constraint) in av.iter().enumerate() {
                    if i == av.len() - 1 {
                        write!(f, "{}", constraint)?;
                    } else {
                        write!(f, "{},", constraint)?;
                    }
                }
                write!(f, " )")
            }
        }
    }
}

pub fn unify_wrap(
    av: &Vec<ASTValue>,
    bv: &Vec<ASTValue>,
    bindings: Arc<Bindings>,
) -> Option<Arc<Bindings>> {
    let inner = (*bindings).clone();

    lax_unify(av, bv, inner).ok().map(|x| Arc::new(x))
}

pub fn lax_unify_wrap(
    av: &Vec<ASTValue>,
    bv: &Vec<ASTValue>,
    bindings: Arc<Bindings>,
) -> Result<Arc<Bindings>, Arc<Bindings>> {
    let inner = (*bindings).clone();
    lax_unify(av, bv, inner).map_or_else(|x| Err(Arc::new(x)), |x| Ok(Arc::new(x)))
}

pub fn lax_unify(
    av: &Vec<ASTValue>,
    bv: &Vec<ASTValue>,
    bindings: Bindings,
) -> Result<Bindings, Bindings> {
    let mut new_bindings = bindings.clone();
    for (i, j) in av.into_iter().zip(bv) {
        use ASTValue::*;
        match (i, j) {
            (Literal(x), Literal(y)) => {
                if x == y {
                    continue;
                } else {
                    return Err(new_bindings);
                }
            }
            (Variable(x), vy @ Literal(_)) => {
                if let Some(vx) = new_bindings.get(x) {
                    let partials = lax_unify(&vec![vx.clone()], &vec![vy.clone()], new_bindings);
                    if let Ok(binds) = partials {
                        new_bindings = binds;
                    } else {
                        return partials;
                    }
                } else {
                    new_bindings.insert(x.clone(), vy.clone());
                }
            }
            (vx @ Literal(_), Variable(y)) => {
                if let Some(vy) = new_bindings.get(y) {
                    let partials = lax_unify(&vec![vx.clone()], &vec![vy.clone()], new_bindings);
                    if let Ok(binds) = partials {
                        new_bindings = binds;
                    } else {
                        return partials;
                    }
                } else {
                    new_bindings.insert(y.clone(), vx.clone());
                }
            }
            (Variable(x), Variable(y)) => {
                let vy = Variable(y.clone());
                new_bindings.insert(x.clone(), vy);
            }
            (
                Literal(DBValue::List(list)),
                PatternMatch {
                    explicit_values,
                    is_glob,
                    glob_position,
                },
            ) => {
                let partials = unify_pattern_match(
                    list,
                    explicit_values,
                    is_glob,
                    glob_position,
                    new_bindings,
                );
                if let Ok(binds) = partials {
                    new_bindings = binds;
                } else {
                    return partials;
                }
            }
            (
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
                    new_bindings,
                );
                if let Ok(binds) = partials {
                    new_bindings = binds;
                } else {
                    return partials;
                }
            }
            _ => {
                return Err(new_bindings);
            }
        }
    }
    Ok(new_bindings)
}

pub fn unify_pattern_match(
    list: &Vec<DBValue>,
    explicit_values: &Vec<ASTValue>,
    is_glob: &bool,
    glob_position: &GlobPosition,
    new_bindings: Bindings,
) -> Result<Bindings, Bindings> {
    use ASTValue::*;
    let partials = if !is_glob {
        lax_unify(
            &explicit_values,
            &list.clone().into_iter().map(|x| Literal(x)).collect(),
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

type BindingsIterator<'a> = Box<dyn Iterator<Item = Result<Arc<Bindings>, Arc<Bindings>>> + 'a>;

pub struct InnerFactPossibilitiesIter {
    pub database: Arc<Database>,
    pub id: RelationID,
    pub bindings: Arc<Bindings>,
    pub tokens: Vec<ASTValue>,
    fact_index: usize,
}

impl InnerFactPossibilitiesIter {
    pub fn new(
        id: RelationID,
        tokens: Vec<ASTValue>,
        database: Arc<Database>,
        bindings: Arc<Bindings>,
    ) -> Self {
        Self {
            id,
            database,
            bindings,
            tokens,
            fact_index: 0,
        }
    }
}

impl Iterator for InnerFactPossibilitiesIter {
    type Item = Result<Arc<Bindings>, Arc<Bindings>>;
    fn next(&mut self) -> Option<Self::Item> {
        if let Some(facts) = self.database.facts.get(&self.id) {
            if self.fact_index < facts.len() {
                let fact = &facts[self.fact_index];
                let fact_tokens = fact.iter().map(|x| ASTValue::Literal(x.clone())).collect();
                self.fact_index += 1;
                Some(lax_unify_wrap(
                    &self.tokens,
                    &fact_tokens,
                    self.bindings.clone(),
                ))
            } else {
                None
            }
        } else {
            None
        }
    }
}

pub struct PossibleBindings<'b> {
    pub constraint: Arc<Constraint>,
    pub database: Arc<Database>,
    pub bindings: Arc<Bindings>,
    current_fact_possibilities: BindingsIterator<'b>,
    current_rule_possibilities: BindingsIterator<'b>,
    done: bool,
}

impl<'b> PossibleBindings<'b> {
    pub fn new(
        constraint: Arc<Constraint>,
        database: Arc<Database>,
        bindings: Arc<Bindings>,
    ) -> Self {
        Self {
            constraint,
            database,
            bindings,
            current_fact_possibilities: Box::new(empty()),
            current_rule_possibilities: Box::new(empty()),
            done: false,
        }
    }
    pub fn new_with_bindings(
        constraint: Arc<Constraint>,
        database: Arc<Database>,
        bindings: Arc<Bindings>,
        possibilities: Vec<Arc<Bindings>>,
    ) -> Self {
        Self {
            constraint,
            database,
            bindings,
            current_fact_possibilities: Box::new(possibilities.into_iter().map(|x| Ok(x))),
            current_rule_possibilities: Box::new(empty()),
            done: true,
        }
    }
}

impl<'b> Iterator for PossibleBindings<'b> {
    type Item = Result<Arc<Bindings>, Arc<Bindings>>;

    fn next(&mut self) -> Option<Self::Item> {
        use Constraint::*;
        if let Some(binding) = self.current_fact_possibilities.next() {
            Some(binding)
        } else if let Some(binding) = self.current_rule_possibilities.next() {
            Some(binding)
        } else if !self.done {
            match self.constraint.as_ref() {
                Relation(id, tokens) => {
                    self.current_fact_possibilities = Box::new(InnerFactPossibilitiesIter::new(
                        id.to_string(),
                        tokens.to_vec(),
                        self.database.clone(),
                        self.bindings.clone(),
                    ));
                    let db = self.database.rules.read().unwrap();
                    let val = db.get(id);
                    if let Some((params, constraints)) = val {
                        println!("{:?}", constraints);
                        if let Some(args) = unify_wrap(&tokens, &params, self.bindings.clone()) {
                            let possible_binds = BacktrackingQuery::new(
                                constraints.into_iter().map(|a| a.clone()).collect(),
                                self.database.clone(),
                                args.clone(),
                            )
                            .map(|x| Ok(x));
                            self.current_rule_possibilities = Box::new(possible_binds);
                        }
                    }
                }

                Comparison(op, a, b) => {
                    if unify_compare(&op, &a, &b, self.bindings.clone()) {
                        self.current_fact_possibilities =
                            Box::new(vec![Ok(self.bindings.clone())].into_iter());
                    } else {
                        self.current_fact_possibilities = Box::new(empty());
                    }
                }

                Unification(avs, bvs) => {
                    if let Some(new_bindings) = unify_wrap(avs, bvs, self.bindings.clone()) {
                        self.current_fact_possibilities =
                            Box::new(vec![Ok(new_bindings)].into_iter());
                    } else {
                        self.current_fact_possibilities = Box::new(empty());
                    }
                }

                Not(constraint) => {
                    let shadow_binding = self.bindings.clone();
                    let shadow_database = self.database.clone();
                    self.current_fact_possibilities = Box::new(
                        PossibleBindings::new(
                            (*constraint).clone().into(),
                            shadow_database.clone(),
                            shadow_binding.clone(),
                        )
                        .map(|x| {
                            println!("{:?}", x);
                            x.map_or_else(|x| Ok(x), |x| Err(x))
                        }),
                    );
                }

                Alternatives(av) => {
                    let shadow_binding = self.bindings.clone();
                    let shadow_database = self.database.clone();
                    let possibilities = construct_alternatives(
                        av.clone(),
                        shadow_database.clone(),
                        shadow_binding.clone(),
                    );
                    self.current_fact_possibilities = Box::new(possibilities);
                }
                Intersections(av) => {
                    let possible_binds = BacktrackingQuery::new(
                        av.into_iter().map(|a| Arc::new(a.clone())).collect(),
                        self.database.clone(),
                        self.bindings.clone(),
                    )
                    .map(|x| Ok(x));
                    self.current_fact_possibilities = Box::new(possible_binds);
                }
                _ => unimplemented!(),
            }
            self.done = true;
            if let Some(binding) = self.current_fact_possibilities.next() {
                Some(binding)
            } else if let Some(binding) = self.current_rule_possibilities.next() {
                Some(binding)
            } else {
                None
            }
        } else {
            None
        }
    }
}

fn construct_alternatives<'a>(
    av: Vec<Constraint>,
    database: Arc<Database>,
    bindings: Arc<Bindings>,
) -> impl Iterator<Item = Result<Arc<Bindings>, Arc<Bindings>>> {
    av.into_iter()
        .flat_map(move |a| PossibleBindings::new(Arc::new(a), database.clone(), bindings.clone()))
}
