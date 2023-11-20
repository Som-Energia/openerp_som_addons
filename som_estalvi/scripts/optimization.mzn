int: nMesos = 12;
int: nPeriodes = 6;
float: preuPenalitzacio;
bool: es61;

array[1..nMesos, 1..nPeriodes] of int: potenciaMax;
array[1..nPeriodes] of float: preuPotencies;
array[1..nPeriodes] of var 1..max(potenciaMax): potenciaOptima;
array[1..12] of int: diesMes = [31,29,31,30,31,30,31,31,30,31,30,31];
array[1..nMesos,1..nPeriodes] of var 0..max(potenciaMax)*max(preuPotencies): maximetreMesPeriode;
array[1..nPeriodes] of var 0..max(potenciaMax)*max(preuPotencies): totalMaximetres;
array[1..nPeriodes] of var 0..max(potenciaMax)*max(preuPotencies): totalPotencies;
% var float: totalCost = sum(totalMaximetres) + sum(totalPotencies) + costAugmentPotencies;
var float: totalCost = sum(totalMaximetres) + sum(totalPotencies);

constraint potenciaOptima[1] <= potenciaOptima[2];
constraint potenciaOptima[2] <= potenciaOptima[3];
constraint potenciaOptima[3] <= potenciaOptima[4];
constraint potenciaOptima[4] <= potenciaOptima[5];
constraint potenciaOptima[5] <= potenciaOptima[6];

%predicate increasing(potenciaOptima);

%esta malament com "emplenem" total maximetres
constraint forall(i in 1..nMesos, j in 1..nPeriodes) ((potenciaMax[i,j]-potenciaOptima[j] > 0) -> (maximetreMesPeriode[i,j] = (potenciaMax[i,j]-potenciaOptima[j]) * diesMes[i] * preuPenalitzacio * 2));

constraint forall(i in 1..nPeriodes) (totalMaximetres[i] = sum(col(maximetreMesPeriode,i)));
constraint forall(i in 1..nPeriodes) (totalPotencies[i] = potenciaOptima[i] * preuPotencies[i]);
constraint min(potenciaOptima) >= 15 \/ es61;

solve minimize totalCost;


output ["\n\n Cost: " ++ show(totalCost) ++ " euros"];
output ["\n\n potenciesOptimes: " ++ show(potenciaOptima[i]) |
         i in 1..nPeriodes
    ];

output ["\n\n totalMaximetres: " ++ show(totalMaximetres[i]) |
         i in 1..nPeriodes
    ];

output ["\n\n totalPotencies: " ++ show(totalPotencies[i]) |
         i in 1..nPeriodes
    ];