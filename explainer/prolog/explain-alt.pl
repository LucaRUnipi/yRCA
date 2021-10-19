:-set_prolog_flag(last_call_optimisation, true).

%determine "NumSols" possible explanations for "Event"
xfail(NumSols,Event,Explanations,RootCause) :-
    findnsols(NumSols,E,distinct(causedBy(Event,E,RootCause)),Explanations).
    
%invoked service never started
causedBy(log(_,S,T,_,_,_),[X],N) :-
    log(_,S,Ts,sendTo(N,_),_,_), Ts < T, lookbackRadius(Z), Ts >= T - Z,
    \+ log(N,_,_,_,_,_),
    X = neverStarted(N).
%unreachable service
causedBy(log(_,S,T,_,_,_),[X],N) :-
    unhandledRequest(S,N,Ts,_), Ts < T, lookbackRadius(Z), Ts >= T - Z,
    log(N,_,_,_,_,_),
    X = unreachable(N).
%error of invoked service
causedBy(log(_,S,T,_,_,_),[X|Xs],R) :-
    interaction(S,S2,Ts,Te), Ts < T, lookbackRadius(Z), Ts >= T - Z,
    log(N,S2,U,F,M,Sev), lte(Sev,warning), Ts =< U, U =< Te, 
    X=log(N,S2,U,F,M,Sev),
    causedBy(X,Xs,R).

%ci serve la regola "crash of invoked service"? non basterebbe distinguere i casi "interazione" da "interazione senza risposta" (che potremmo distinguere con due tipi diversi di interaction)
%Osservazione: A interagisce con B, quattro possibili casi:
% 1) B non ha creato problemi -> scarto B dalle cause
% 2) B ha loggato errore -> catturato da regola sopra
% 3) B ha risposto con errore -> catturato dal fatto che A loggherà tale errore 
% 4) B ha gestito la richiesta, ma non ha mai risposto -> catturato da regola sotto, ma insieme a moltri altri casi (basta vedere se ha mai risposto)
%crash of invoked service
causedBy(log(_,S,T,_,_,_),[X],N) :-
    interaction(S,S2,Ts,Te), Ts < T, lookbackRadius(Z), Ts >= T - Z,
    heartbeat(P), T0 is Ts - P, T1 is Te + P,
    once((log(N,S2,U,_,_,_), T0=<U, U=<T1, \+ (log(_,S2,V,_,_,_), dif(U,V), U-P=<V, V=<U+P))),
    X = failed(N,S2). 

%ci serve la regola "internal crash"? perché spiegare che A ha loggato qualcosa dicendo che prima non aveva loggato niente?
%internal crash
causedBy(log(N,S,T,_,_,_),[X],N) :-
    heartbeat(P), T0 is T-P, T0>0,
    \+ (log(_,S,U,_,_,_), T0 =< U, U < T),
    X = failed(N,S). 

%base case
causedBy(log(N,_,_,_,_,_),[],N).
%causedBy(log(N,S,_,_,_,_),[failed(N,S)],N). % da usare se togliamo "internal crash"

lte(S1,S2) :- severity(S1,A), severity(S2,B), A=<B.

interaction(S1,S2,Ts,Te) :-
    log(N1,S1,Ts,sendTo(N2,Id),_,_), 
    log(N2,S2,_,received(Id),_,_),
    log(N1,S1,Te,answerFrom(N2,Id),_,_). %, Ts < Te.

%modellare interazione fallita?
%interaction(S1,S2,Ts,Te) :-
%    log(N1,S1,Ts,sendTo(N2,Id),_,_), 
%    log(N2,S2,_,received(Id),_,_),
%    log(N1,S1,Te,timeout(N2,Id),_,_). %, Ts < Te.

%TODO
%interaction(S1,N2,Ts,Te)
%interazione tra servizio S1 e nodo N2 con logging non configurato (e.g., database, message queue)

unhandledRequest(S1,N2,Ts,Te) :-
    log(N1,S1,Ts,sendTo(N2,Id),_,_),
    \+ log(N2,_,_,received(Id),_,_),
    log(N1,S1,Te,answerFrom(N2,Id),_,_). %, Ts < Te.
    %timeout anche qui?