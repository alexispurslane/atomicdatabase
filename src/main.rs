use std::env;
use std::fs::{read_to_string, OpenOptions};
use std::io::prelude::*;
use std::os::unix::prelude::FileExt;
use std::{collections::HashMap, sync::Arc};

use database::{backtracking::BacktrackingQuery, parser::parse_fact, Database};
use rustyline::error::ReadlineError;

use crate::database::parser::{parse_file, parse_line, tokenize_line, tokens_to_values};

mod database;

macro_rules! fact {
    ($db: ident, $($t:tt)*) => {
        $db.insert_fact(parse_fact(stringify!($($t)*).to_string()).unwrap())
    };
}

macro_rules! query {
    ($($t:tt)+) => {
        vec![Arc::new(parse_line(stringify!($($t)*).to_string()).unwrap())]
    }
}

macro_rules! rule {
    ($db:ident, $name:ident ( $($a:ident)+ ) => $($t:tt)+) => {
        $db.insert_rule(
            stringify!($name).to_string().to_uppercase(),
            tokens_to_values(&tokenize_line(stringify!($($a)+).to_string()).unwrap()).unwrap(),
            query!($($t)+),
        )?;
    }
}

static GREEN_MESSAGE: &'static str = "\x1b[1;32m";
static NORMAL: &'static str = "\x1b[0m";
static RED_MESSAGE: &'static str = "\x1b[1;31m";
static GRAY_MESSAGE: &'static str = "\x1b[38;5;247m";

fn main() -> Result<(), String> {
    let db = Arc::new(Database::new());
    let bindings = Arc::new(HashMap::new());

    let rl_config = rustyline::Config::builder()
        .completion_type(rustyline::config::CompletionType::List)
        .edit_mode(rustyline::config::EditMode::Vi)
        .bell_style(rustyline::config::BellStyle::Visible)
        .tab_stop(4)
        .indent_size(4)
        .check_cursor_position(true)
        .build();
    let mut rl = rustyline::DefaultEditor::with_config(rl_config)
        .map_err(|_| "Could not start readline REPL!".to_string())?;
    if rl.load_history(".atomic_history").is_err() {
        println!("No previous history.");
    }

    // FIXME: databases should not be stored this way. It's slow as fuck. Find a
    // better way
    let mut dbfacts = OpenOptions::new()
        .append(true)
        .read(true)
        .create(true)
        .open(
            env::args()
                .collect::<Vec<_>>()
                .get(1)
                .unwrap_or(&"default_knowledgebase".to_string()),
        )
        .unwrap();

    let mut dbstring = String::new();
    let _ = dbfacts
        .read_to_string(&mut dbstring)
        .map_err(|_| "Couldn't read from database file!")?;

    println!("Reading from file...");
    let meta_ast = parse_file(dbstring)?;
    for statement in meta_ast {
        let query = Database::evaluate(db.clone(), bindings.clone(), statement)?;
        if let Some(query) = query {
            explore_query(&mut rl, query, false)?;
        }
    }

    print_banner();

    println!("{} relations in knowledge base schema", db.facts.len());
    println!(
        "{} facts loaded",
        db.facts
            .iter()
            .map(|entry| entry.value().len())
            .sum::<usize>()
    );
    println!("{} rules loaded", db.rules.read().unwrap().len());

    loop {
        let readline = rl.readline(">> ");

        match readline {
            Ok(line) => {
                let mut line = line.to_string();
                if line.starts_with(".") {
                    line.remove(0);
                    if line.starts_with("fact ") {
                        line.drain(0..5);
                        let parse = parse_fact(line.clone()).and_then(|fact| db.insert_fact(fact));
                        if let Ok(_) = parse {
                            let _ = writeln!(dbfacts, "{}", line)
                                .map_err(|_| "Cannot save new fact to in memory fact file")?;
                        } else {
                            println!("{}Error: {}{}", RED_MESSAGE, parse.unwrap_err(), NORMAL);
                        }
                    } else if line == "save" {
                        dbfacts
                            .flush()
                            .map_err(|_| "Cannot flush in memory fact file to disk")?;
                    } else if line == "exit" {
                        println!("Bye!");
                        break;
                    } else if line == "help" {
                        println!(
                            r"
REPL commands:

.{}fact{} <valid db fact> --- adds a new fact to the in-memory database
.{}save{}                 --- saves a literal readout of the commands to
                          build the in-memory database to disk, for
                          loading at startup
.{}exit{}                 --- exits the repl (CTRL-C and CTRL-D also work)
.{}help{}                 --- this help message

Query language:

All other inputs at the REPL are interpreted as queries. Queries have the
following syntax:

query:      <literal/variable> <relation-id> <any number of literals or variables>
either-or:  <query>; <query>; ..
both-and:   <query>, <query>, ..
unify:      <literals/variables> ~ <literals/variables>
not:        !<query>
comparison: <literal/variable> <operator> <literal/variable>
group:      (<query>)
operator: < > <= >= =
",
                            GREEN_MESSAGE,
                            NORMAL,
                            GREEN_MESSAGE,
                            NORMAL,
                            GREEN_MESSAGE,
                            NORMAL,
                            GREEN_MESSAGE,
                            NORMAL
                        )
                    } else {
                        println!("Unrecognized repl command.");
                    }
                } else {
                    rl.add_history_entry(line.clone())
                        .map_err(|_| "Cannot save history")?;
                    let parse = parse_line(line);
                    if let Ok(parse) = parse {
                        let constraint = Arc::new(parse);

                        println!("=>{}{}{}", GRAY_MESSAGE, constraint, NORMAL);

                        let query =
                            BacktrackingQuery::new(vec![constraint], db.clone(), bindings.clone());

                        explore_query(&mut rl, query, true);
                    } else {
                        println!("{}Error: {}{}", RED_MESSAGE, NORMAL, parse.unwrap_err());
                    }
                }
            }
            Err(rustyline::error::ReadlineError::Interrupted) => {
                println!("CTRL-C");
                break;
            }
            Err(rustyline::error::ReadlineError::Eof) => {
                println!("CTRL-D");
                break;
            }
            Err(err) => {
                println!("{}Error: {}{}", RED_MESSAGE, err, NORMAL);
                break;
            }
        }
    }

    rl.save_history(".atomic_history")
        .map_err(|x| format!("{:?}", x))?;

    Ok(())
}

fn explore_query<'a>(
    rl: &mut rustyline::DefaultEditor,
    query: BacktrackingQuery<'a>,
    confirm_continue: bool,
) -> Result<(), String> {
    for (i, solution) in query.enumerate() {
        println!("{}Solution {}: {}", GREEN_MESSAGE, i, NORMAL);
        for (k, v) in solution.iter() {
            println!("    {} ~ {}", k, v);
        }
        if confirm_continue {
            let confirm = rl
                .readline("(press enter for next solution, n to stop)>> ")
                .map_err(|_| "Can't prompt with readline!")?;
            if confirm.to_lowercase().contains("n") {
                break;
            } else {
                print!("{}", "\x1b[s\x1b[1A\x1b[2K\x1b[u");
            }
        }
    }
    Ok(())
}

fn print_banner() {
    println!(
        r"
 _______ _________ _______  _______ _________ _______  ______   ______
(  ___  )\__   __/(  ___  )(       )\__   __/(  ____ \(  __  \ (  ___ \
| (   ) |   ) (   | (   ) || () () |   ) (   | (    \/| (  \  )| (   ) )
| (___) |   | |   | |   | || || || |   | |   | |      | |   ) || (__/ /
|  ___  |   | |   | |   | || |(_)| |   | |   | |      | |   | ||  __ (
| (   ) |   | |   | |   | || |   | |   | |   | |      | |   ) || (  \ \
| )   ( |   | |   | (___) || )   ( |___) (___| (____/\| (__/  )| )___) )
|/     \|   )_(   (_______)|/     \|\_______/(_______/(______/ |/ \___/
                                     {}Welcome to ATOMIC DB v3.0 Alpha 1{}

",
        GREEN_MESSAGE, NORMAL
    );
}
