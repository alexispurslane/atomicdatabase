use std::borrow::Cow;
use std::rc::Rc;

use super::unification::{chain_hashmap, Bindings, Constraint, PossibleBindings};
use super::Database;

pub struct BacktrackingQuery<'a> {
    pub constraints: &'a [Constraint],
    pub database: Rc<Database>,
    pub bindings: Rc<Bindings>,
    constraint_stack: Vec<(&'a Constraint, PossibleBindings<'a>)>,
}

impl<'a> BacktrackingQuery<'a> {
    pub fn new(
        constraints: &'a [Constraint],
        database: Rc<Database>,
        bindings: Rc<Bindings>,
    ) -> Self {
        BacktrackingQuery {
            constraints,
            database,
            bindings,
            constraint_stack: Vec::with_capacity(constraints.len()),
        }
    }
}

impl Iterator for BacktrackingQuery<'_> {
    type Item = Rc<Bindings>;

    fn next(&mut self) -> Option<Rc<Bindings>> {
        loop {
            // Satisfy all the constraints
            if let Some(new_constraint) = self.constraints.get(self.constraint_stack.len()) {
                let mut only_possible = PossibleBindings::new_with_bindings(
                    new_constraint,
                    self.database.clone(),
                    self.bindings.clone(),
                    vec![self.bindings.clone()],
                );
                let last_possible_bindings = self
                    .constraint_stack
                    .last_mut()
                    .map_or(&mut only_possible, |(_lc, cb)| cb);
                if let Some(possible_binding) = last_possible_bindings.next() {
                    if let Ok(possible_binding) = possible_binding {
                        // possible bindings for this next branch given the next possible binding for the previous branch
                        println!("New assumption for constraint given previous");
                        let new_possible_bindings = PossibleBindings::new(
                            new_constraint,
                            self.database.clone(),
                            possible_binding.clone(),
                        );
                        self.constraint_stack
                            .push((new_constraint, new_possible_bindings));
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
                if let Some((_lc, lbs)) = self.constraint_stack.last_mut() {
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
