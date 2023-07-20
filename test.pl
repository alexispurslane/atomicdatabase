father(abraham, benjamin).
father(adam, bob).
father(aaron, bob).

partners(X,Y) :-
    father(X,T),
    father(Y,T).
