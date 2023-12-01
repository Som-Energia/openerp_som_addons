int: nMesos = 12;
int: nPeriodes = 6;
float: excess_price;
bool: contract61;
int: power_p6;
int: max_power = max(max(maximeters_powers),power_p6);

array[1..nMesos, 1..nPeriodes] of int: maximeters_powers;
array[1..nPeriodes] of float: power_price;
array[1..nPeriodes] of var 1..max_power: potenciaOptima;
array[1..12] of int: diesMes = [31,29,31,30,31,30,31,31,30,31,30,31];
array[1..nMesos,1..nPeriodes] of var 0..max(maximeters_powers)*max(power_price): maximetreMesPeriode;
array[1..nPeriodes] of var 0..max(maximeters_powers)*max(power_price): totalMaximetres;
array[1..nPeriodes] of var 0..max_power*max(power_price): totalPotencies;
var float: totalCost = sum(totalMaximetres) + sum(totalPotencies);

constraint power_p6 <= potenciaOptima[6];
constraint potenciaOptima[1] <= potenciaOptima[2];
constraint potenciaOptima[2] <= potenciaOptima[3];
constraint potenciaOptima[3] <= potenciaOptima[4];
constraint potenciaOptima[4] <= potenciaOptima[5];
constraint potenciaOptima[5] <= potenciaOptima[6];
constraint (max(potenciaOptima) >= 15) \/ contract61;

constraint forall(i in 1..nMesos, j in 1..nPeriodes) ((maximeters_powers[i,j]-potenciaOptima[j] > 0) -> (maximetreMesPeriode[i,j] = (maximeters_powers[i,j]-potenciaOptima[j]) * diesMes[i] * excess_price * 2));

constraint forall(i in 1..nPeriodes) (totalMaximetres[i] = sum(col(maximetreMesPeriode,i)));
constraint forall(i in 1..nPeriodes) (totalPotencies[i] = potenciaOptima[i] * power_price[i]);

solve minimize totalCost;

output ["'{\"totalCost\": " ++ show(totalCost)];
output [", \"optimalPowers\": " ++ showJSON(potenciaOptima)];
output [", \"totalMaximeters\": " ++ showJSON(totalMaximetres)];
output [", \"totalPowers\": " ++ showJSON(totalPotencies) ++ "}'"];
