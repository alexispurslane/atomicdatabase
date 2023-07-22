use std::fmt;
use std::fmt::Debug;
use std::marker::PhantomData;
use std::sync::Arc;
use std::sync::RwLock;
use std::sync::RwLockReadGuard;

use super::unification::*;
use super::ASTValue;
use super::Database;
use std::iter::empty;

use std::collections::HashMap;

#[derive(Debug, Clone, PartialEq)]
pub enum Constraint {
    Relation(RelationID, Vec<ASTValue>),
    Unification(Vec<ASTValue>, Vec<ASTValue>),
    Comparison(EqOp, ASTValue, ASTValue),
    Not(Box<Constraint>),
    Alternatives(Vec<Constraint>),
    Intersections(Vec<Constraint>),
    Fail,
    Succeed,
}

impl fmt::Display for Constraint {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        use Constraint::*;
        match self {
            Relation(rel, values) => {
                write!(f, "{} <{}>", values[0], rel)?;
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
            Fail => write!(f, "FAIL"),
            Succeed => write!(f, "SUCCEED"),
        }
    }
}

pub struct BacktrackingQuery<'a> {
    // FIXME: Constraints should NOT require shared ownership, as far as I can tell
    pub constraints: Vec<Arc<Constraint>>,
    pub database: Arc<Database>,
    pub bindings: Arc<Bindings>,
    constraint_stack: Vec<PossibleBindings<'a>>,
    depth: usize,
}

impl<'a> BacktrackingQuery<'a> {
    pub fn new(
        constraints: Vec<Arc<Constraint>>,
        database: Arc<Database>,
        bindings: Arc<Bindings>,
    ) -> Self {
        let len = constraints.len();
        BacktrackingQuery {
            constraints,
            database,
            bindings,
            constraint_stack: Vec::with_capacity(len),
            depth: 0,
        }
    }

    pub fn new_depth(
        constraints: Vec<Arc<Constraint>>,
        database: Arc<Database>,
        bindings: Arc<Bindings>,
        depth: usize,
    ) -> Self {
        let len = constraints.len();
        BacktrackingQuery {
            constraints,
            database,
            bindings,
            constraint_stack: Vec::with_capacity(len),
            depth: depth + 1,
        }
    }
}

impl Debug for BacktrackingQuery<'_> {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "Query (\n")?;
        for constraint in self.constraints.iter() {
            write!(f, "    {}.\n", constraint)?;
        }
        write!(f, ")")
    }
}

impl Iterator for BacktrackingQuery<'_> {
    type Item = Arc<Bindings>;

    fn next(&mut self) -> Option<Arc<Bindings>> {
        loop {
            let current_constraint_index = self.constraint_stack.len();
            // Satisfy all the constraints
            if let Some(new_constraint) = self.constraints.get(current_constraint_index) {
                let last_binding = self
                    .constraint_stack
                    .last_mut()
                    .map_or(Some(Ok(self.bindings.clone())), |x| x.next());
                if let Some(last_binding) = last_binding {
                    if let Ok(environment) = last_binding {
                        // println!(
                        //     " {}>: {} {}",
                        //     (0..(self.constraint_stack.len() + self.depth))
                        //         .map(|_| '-')
                        //         .collect::<String>(),
                        //     new_constraint,
                        //     fmt_arc_bindings(environment.clone())
                        // );
                        // possible bindings for this next branch given the next possible binding for the previous branch
                        let new_possible_bindings = PossibleBindings::new(
                            new_constraint.clone(),
                            self.database.clone(),
                            environment.clone(),
                            self.depth,
                        );
                        self.constraint_stack.push(new_possible_bindings);
                    } else {
                        // we don't do that here (for now)
                        // TODO: partial mode?
                    }
                } else {
                    // This branch is exhausted, go up!
                    self.constraint_stack.pop();
                    if self.constraint_stack.is_empty() {
                        // We've exhausted even the first constraint, so we're done here
                        return None;
                    }
                }
            } else {
                // All constraints satisfied on this branch (we've gone as deep
                // as we can) So return next possible value from the end of this
                // branch! If we've run out of possible values, go up a branch
                // and try more possible values there to produce more here
                if let Some(lbs) = self.constraint_stack.last_mut() {
                    if let Some(binding) = lbs.next() {
                        if let Ok(binding) = binding {
                            return Some(binding);
                        } else {
                            // we don't do that here
                            // TODO 2, electric boogaloo
                        }
                    } else {
                        self.constraint_stack.pop();
                        if self.constraint_stack.is_empty() {
                            // We've exhausted even the first constraint, so we're done here
                            return None;
                        }
                    }
                } else {
                    // If we end up here, that means we were given an empty constraint slice
                    return None;
                }
            }
        }
    }
}

pub type BindingsIterator<'a> = Box<dyn Iterator<Item = Result<Arc<Bindings>, Arc<Bindings>>> + 'a>;

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
                let var = lax_unify(
                    &self.tokens,
                    &fact_tokens,
                    (*self.bindings).clone(),
                    &self.bindings,
                )
                .map_or_else(|x| Err(Arc::new(x)), |x| Ok(Arc::new(x)));
                Some(var)
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
    depth: usize,
) -> impl Iterator<Item = Result<Arc<Bindings>, Arc<Bindings>>> {
    av.into_iter().flat_map(move |a| {
        PossibleBindings::new(Arc::new(a), database.clone(), bindings.clone(), depth)
    })
}

pub struct PossibleBindings<'b> {
    pub constraint: Arc<Constraint>,
    pub database: Arc<Database>,
    pub bindings: Arc<Bindings>,
    current_fact_possibilities: BindingsIterator<'b>,
    current_rule_possibilities: BindingsIterator<'b>,
    constraints_done: bool,
    rules_index: usize,
    depth: usize,
}

impl<'b> PossibleBindings<'b> {
    pub fn new(
        constraint: Arc<Constraint>,
        database: Arc<Database>,
        bindings: Arc<Bindings>,
        depth: usize,
    ) -> Self {
        Self {
            constraint,
            database,
            bindings,
            current_fact_possibilities: Box::new(empty()),
            current_rule_possibilities: Box::new(empty()),
            constraints_done: false,
            rules_index: 0,
            depth: depth + 1,
        }
    }

    pub fn new_with_bindings(
        constraint: Arc<Constraint>,
        database: Arc<Database>,
        bindings: Arc<Bindings>,
        possibilities: Vec<Arc<Bindings>>,
        depth: usize,
    ) -> Self {
        Self {
            constraint,
            database,
            bindings,
            current_fact_possibilities: Box::new(possibilities.into_iter().map(|x| Ok(x))),
            current_rule_possibilities: Box::new(empty()),
            constraints_done: true,
            rules_index: 0,
            depth: depth + 1,
        }
    }

    fn get_possible_rule<'a>(
        &self,
        db_rules: &'a RwLockReadGuard<
            HashMap<RelationID, Vec<(Vec<ASTValue>, Vec<Arc<Constraint>>)>>,
        >,
    ) -> Option<&'a (Vec<ASTValue>, Vec<Arc<Constraint>>)> {
        if let Constraint::Relation(id, _) = self.constraint.as_ref() {
            db_rules.get(id).and_then(|x| x.get(self.rules_index))
        } else {
            None
        }
    }
}

impl<'b> Iterator for PossibleBindings<'b> {
    type Item = Result<Arc<Bindings>, Arc<Bindings>>;

    fn next(&mut self) -> Option<Self::Item> {
        use Constraint::*;

        let db = self.database.clone();
        let db_rules = db.rules.read().unwrap();
        let possible_rule = self.get_possible_rule(&db_rules);

        if let Some(binding) = self.current_fact_possibilities.next() {
            Some(binding)
        } else if let Some(binding) = self.current_rule_possibilities.next() {
            Some(binding)
        } else if !self.constraints_done || possible_rule.is_some() {
            match self.constraint.as_ref() {
                Relation(id, tokens) => {
                    self.current_fact_possibilities = Box::new(InnerFactPossibilitiesIter::new(
                        id.to_string(),
                        tokens.to_vec(),
                        self.database.clone(),
                        self.bindings.clone(),
                    ));
                    if let Some((params, constraints)) = possible_rule {
                        let args = split_arguments(&tokens, &params, self.bindings.clone());
                        if let Ok((outer_args, inner_args)) = args {
                            let possible_binds = BacktrackingQuery::new_depth(
                                constraints.into_iter().map(|a| a.clone()).collect(),
                                self.database.clone(),
                                Arc::new(inner_args),
                                self.depth,
                            )
                            .map(reduce_and_eliminate_wrap(
                                Arc::new(outer_args),
                                self.bindings.clone(),
                            ));
                            self.current_rule_possibilities = Box::new(possible_binds);
                        }
                        self.rules_index += 1;
                    }
                }

                Comparison(op, a, b) => {
                    if unify_compare(&op, &a, &b, self.bindings.clone()) {
                        self.current_fact_possibilities =
                            Box::new(vec![Ok(self.bindings.clone())].into_iter());
                    } else {
                        self.current_fact_possibilities =
                            Box::new(vec![Err(self.bindings.clone())].into_iter());
                    }
                }

                Unification(avs, bvs) => {
                    self.current_fact_possibilities = Box::new(
                        vec![
                            lax_unify(avs, bvs, (*self.bindings).clone(), &self.bindings)
                                .map_or_else(|x| Err(Arc::new(x)), |x| Ok(Arc::new(x))),
                        ]
                        .into_iter(),
                    );
                }

                Not(constraint) => {
                    let shadow_binding = self.bindings.clone();
                    let shadow_database = self.database.clone();
                    self.current_fact_possibilities = Box::new(
                        PossibleBindings::new(
                            (*constraint).clone().into(),
                            shadow_database.clone(),
                            shadow_binding.clone(),
                            self.depth,
                        )
                        .map(|x| x.map_or_else(|x| Ok(x), |x| Err(x))),
                    );
                }

                Alternatives(av) => {
                    let shadow_binding = self.bindings.clone();
                    let shadow_database = self.database.clone();
                    let possibilities = construct_alternatives(
                        av.clone(),
                        shadow_database.clone(),
                        shadow_binding.clone(),
                        self.depth,
                    );
                    self.current_fact_possibilities = Box::new(possibilities);
                }
                Intersections(av) => {
                    let possible_binds = BacktrackingQuery::new_depth(
                        av.into_iter().map(|a| Arc::new(a.clone())).collect(),
                        self.database.clone(),
                        self.bindings.clone(),
                        self.depth,
                    )
                    .map(|x| Ok(x));
                    self.current_fact_possibilities = Box::new(possible_binds);
                }
                Fail => {
                    self.current_fact_possibilities =
                        Box::new(vec![Err(self.bindings.clone())].into_iter());
                }
                Succeed => {
                    self.current_fact_possibilities =
                        Box::new(vec![Ok(self.bindings.clone())].into_iter());
                }
            }
            self.constraints_done = true;
            self.next()
        } else {
            None
        }
    }
}

pub fn split_arguments(
    outer_tokens: &Vec<ASTValue>,
    inner_tokens: &Vec<ASTValue>,
    environment: Arc<Bindings>,
) -> Result<(Bindings, Bindings), Bindings> {
    use ASTValue::*;

    let mut outer_bindings = (*environment).clone();
    let mut inner_bindings = HashMap::new();
    for (otok, itok) in outer_tokens.iter().zip(inner_tokens) {
        match (otok, itok) {
            (Variable(_), Literal(_)) => {
                outer_bindings.extend(unify_terms(&otok, &itok, &outer_bindings, &environment).1?);
            }
            (Literal(_), Variable(_)) => {
                inner_bindings.extend(unify_terms(&itok, &otok, &inner_bindings, &environment).1?);
            }
            (outer_var @ Variable(outer_name), inner_var @ Variable(inner_name)) => {
                let throwaway = HashMap::new();
                let outer_val = unify_get_variable_value(outer_name, &outer_bindings, &environment)
                    .unwrap_or(outer_var.clone());
                let inner_val = unify_get_variable_value(inner_name, &inner_bindings, &throwaway)
                    .unwrap_or(inner_var.clone());
                let (hand, binds) = unify_terms(&outer_val, &inner_val, &throwaway, &throwaway);
                let binds = binds?;
                match hand {
                    Hand::Left => {
                        if let Some(outer_bind) = binds.get(outer_name) {
                            outer_bindings.insert(outer_name.clone(), outer_bind.clone());
                        }
                    }
                    Hand::Right => {
                        if let Some(inner_bind) = binds.get(inner_name) {
                            inner_bindings.insert(inner_name.clone(), inner_bind.clone());
                        }
                    }
                    _ => panic!("Got unknown hand for {} ~ {}", otok, itok),
                }
            }
            _ => {
                unify_terms(&otok, &itok, &outer_bindings, &environment).1?;
            }
        }
    }
    // println!(
    //     "{} {}",
    //     fmt_ptr_bindings(&outer_bindings),
    //     fmt_ptr_bindings(&inner_bindings)
    // );
    Ok((outer_bindings, inner_bindings))
}

pub fn reduce_and_eliminate(
    mapping: Arc<Bindings>,
    bindings: Arc<Bindings>,
    environment: Arc<Bindings>,
) -> Bindings {
    let mut new_bindings = (*environment).clone();
    for (varname, varval) in mapping.iter() {
        if let ASTValue::Variable(varname2) = varval {
            if let Some(val) = unify_get_variable_value(varname2, &bindings, &environment) {
                new_bindings.insert(varname.to_string(), val);
            }
        } else if let ASTValue::Literal(_) = varval {
            new_bindings.insert(varname.to_string(), varval.clone());
        }
    }
    new_bindings
}

pub fn reduce_and_eliminate_wrap(
    mapping: Arc<Bindings>,
    environment: Arc<Bindings>,
) -> impl Fn(Arc<Bindings>) -> Result<Arc<Bindings>, Arc<Bindings>> {
    move |x| {
        Ok(Arc::new(reduce_and_eliminate(
            mapping.clone(),
            x.clone(),
            environment.clone(),
        )))
    }
}
