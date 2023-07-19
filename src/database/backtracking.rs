use std::backtrace::Backtrace;
use std::sync::Arc;

use super::unification::{Bindings, Constraint, PossibleBindings};
use super::Database;

pub struct BacktrackingQuery<'a> {
    // FIXME: Constraints should NOT require shared ownership, as far as I can tell
    pub constraints: Vec<Arc<Constraint>>,
    pub database: Arc<Database>,
    pub bindings: Arc<Bindings>,
    constraint_stack: Vec<PossibleBindings<'a>>,
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
        }
    }
}

impl Iterator for BacktrackingQuery<'_> {
    type Item = Arc<Bindings>;

    fn next(&mut self) -> Option<Arc<Bindings>> {
        loop {
            let current_constraint_index = self.constraint_stack.len();
            // Satisfy all the constraints
            if let Some(new_constraint) = self.constraints.get(current_constraint_index) {
                println!("{:?}", new_constraint);
                let mut only_possible = PossibleBindings::new_with_bindings(
                    new_constraint.clone(),
                    self.database.clone(),
                    self.bindings.clone(),
                    vec![self.bindings.clone()],
                );
                let last_possible_bindings = self
                    .constraint_stack
                    .last_mut()
                    .unwrap_or(&mut only_possible);
                if let Some(possible_binding) = last_possible_bindings.next() {
                    if let Ok(possible_binding) = possible_binding {
                        // possible bindings for this next branch given the next possible binding for the previous branch
                        let new_possible_bindings = PossibleBindings::new(
                            new_constraint.clone(),
                            self.database.clone(),
                            possible_binding.clone(),
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
