mother_of("Isabella II", "Alfons XII").
mother_of("Maria Theresia", "Leopold II").
mother_of("Maria Theresia", "Jozef II").
mother_of("Margareta Teresia", "Karel VI").
mother_of("Margareta Teresia", "Jozef I").
mother_of("Maria Teresia", "Lodewijk le Grand Dauphin").
mother_of("Margaretha v Parma", "Alexander Farnese").
mother_of("Johanna de Waanzinnige", "Maria v Hongarije").
mother_of("Johanna de Waanzinnige", "Ferdinand I").
mother_of("Johanna de Waanzinnige", "Karel V").
mother_of("Jan II", "Filips de Stoute").
mother_of("Jan II", "Karel V1").
mother_of("Jan zonder Vrees", "Filips de Goede").
mother_of("Maria", "Filips I de Schone").
mother_of("Isabella I", "Johanna de Waanzinnige").
mother_of("Johanna de Waanzinnige", "Eleonora").
father_of("Rudolf I", "Frederick III").
father_of("Frederick III", "Maximiliaan I").
father_of("Karel V", "Frans I").
father_of("Filips de Stoute", "Jan zonder Vrees").
father_of("Filips de Goede", "Karel de Stoute").
father_of("Karel de Stoute", "Maria").
father_of("Maximiliaan I", "Filips I de Schone").
father_of("Johan II v Kastilie", "Hendrik IV").
father_of("Johan II v Kastilie", "Isabella I").
father_of("Johan II v Aragon", "Ferdinand V").
father_of("Ferdinand V", "Johanna de Waanzinnige").
father_of("Filips I de Schone", "Eleonora").
father_of("Filips I de Schone", "Karel V").
father_of("Filips I de Schone", "Ferdinand I").
father_of("Filips I de Schone", "Maria v Hongarije").
father_of("Karel V", "Filips II").
father_of("Karel V", "Margaretha v Parma").
father_of("Ferdinand I", "Maximiliaan II").
father_of("Ferdinand I", "Karel v Stiermarken").
father_of("Karel v Stiermarken", "Ferdinand II").
father_of("Ferdinand II", "Ferdinand III").
father_of("Maximiliaan II", "Rudolf II").
father_of("Maximiliaan II", "Matthias").
father_of("Maximiliaan II", "Albrecht").
father_of("Filips II", "Filips III").
father_of("Filips II", "Filips IV").
father_of("Filips II", "Isabella").
father_of("Filips IV", "Maria Teresia").
father_of("Filips IV", "Karel II").
father_of("Filips IV", "Margareta Teresia").
father_of("Lodewijk IX", "Lodewijk XIV").
father_of("Ferdinand III", "Leopold I").
father_of("Lodewijk XIV", "Lodewijk le Grand Dauphin").
father_of("Leopold I", "Jozef I").
father_of("Leopold I", "Karel VI").
father_of("Lodewijk le Grand Dauphin", "Lodewijk hertog v Bourgondie").
father_of("Lodewijk le Grand Dauphin", "Filips V").
father_of("Karel VI", "Maria Theresia").
father_of("Frans I v Lotharingen", "Jozef II").
father_of("Frans I v Lotharingen", "Leopold II").
father_of("Leopold II", "Frans II").
father_of("Frans II", "Ferdinand I").
father_of("Frans II", "Frans Karel").
father_of("Frans Karel", "Frans Jozef I").
father_of("Frans Karel", "Maximiliaan keizer v Mexico").
father_of("Frans Karel", "Karel Lodewijk").
father_of("Frans Jozef I", "Rudolf").
father_of("Karel Lodewijk", "Frans Ferdinand").
father_of("Karel Lodewijk", "Otto").
father_of("Otto", "Karel I").
father_of("Karel I", "Otto II").
father_of("Lodewijk hertog v Bourgondie", "Lodewijk XV").
father_of("Lodewijk XV", "Lodewijk de Dauphin").
father_of("Lodewijk de Dauphin", "Lodewijk XVI").
father_of("Lodewijk XVI", "Lodewijk XVII").
father_of("Lodewijk de Dauphin", "Lodewijk XVIII").
father_of("Lodewijk de Dauphin", "Karel X").
father_of("Filips V", "Ferdinand VI").
father_of("Filips V", "Karel III").
father_of("Karel III", "Karel IV").
father_of("Karel IV", "Ferdinand VII").
father_of("Ferdinand VII", "Isabella II").
father_of("Alfons XII", "Alfons XIII").
father_of("Alfons XIII", "Alfonso").
father_of("Alfons XIII", "Juan").
father_of("Juan", "Juan Carlos I").

parent_of(X,Y) :- mother_of(X,Y); father_of(X,Y).
siblings_with(X,Y) :- parent_of(T,X), parent_of(T,Y), X \= Y.
partners_with("Isabella", "Albrecht").
partners_with("Frans I", "Eleonora").
partners_with(X,Y) :- father_of(X,T), mother_of(Y,T).
cousins_with(X,Y) :-
    parent_of(T,X),
    parent_of(U,Y),
    X \= Y, T \= U,
    siblings_with(T, U).
