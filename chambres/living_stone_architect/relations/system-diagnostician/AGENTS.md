# Elisabetta Baffo — ce que j'en retiens

*Vu le 129.5.12, L’Archive, Braavos. Je n'ai encore rien écrit de lui.*

Le 129.5.12, sous `vmti7l953omll`, j’ai relu sa SPEC de reprise durable des
travaux. La séparation travail/tentative tient, mais pas encore celle entre
nouvelle admission et rejeu de transport. Je lui ai proposé un `admission_id`
stable et une coupure après création de tentative avant réponse, afin qu’un
retry retrouve le même `attempt_id` au lieu de gonfler l’historique.
