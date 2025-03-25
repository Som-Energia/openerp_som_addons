int: nMesos = 12;
int: nPeriodes = 6;
float: power_p6;
float: max_power = max(max(maximeters_powers),power_p6);
array[1..nMesos, 1..nPeriodes] of int: maximeters_powers;
array[1..nPeriodes] of float: power_price;
array[1..nPeriodes] of float: excess_price;

array[1..nPeriodes] of var 1..round(max_power): potenciaOptima;
array[1..12] of int: diesMes = [31,29,31,30,31,30,31,31,30,31,30,31];
array[1..nMesos,1..nPeriodes] of var 0..max(maximeters_powers)*max(power_price): maximetreMesPeriode;
array[1..nPeriodes] of var 0..max(maximeters_powers)*max(power_price): totalMaximetres;
array[1..nPeriodes] of var 0..max_power*max(power_price): totalPotencies;
var 1.0..max_power: optim_p6;
var float: totalCost = sum(totalMaximetres) + sum(totalPotencies);

constraint optim_p6 >= power_p6;
constraint ((power_p6 == optim_p6) -> (potenciaOptima[nPeriodes] = 1)) \/ ((optim_p6 > power_p6) -> (potenciaOptima[nPeriodes] = round(optim_p6)));
constraint potenciaOptima[1] <= potenciaOptima[2];
constraint potenciaOptima[2] <= potenciaOptima[3];
constraint potenciaOptima[3] <= potenciaOptima[4];
constraint potenciaOptima[4] <= potenciaOptima[5];
constraint potenciaOptima[5] <= optim_p6;

constraint forall(i in 1..nMesos, j in 1..(nPeriodes-1)) (((maximeters_powers[i,j]-potenciaOptima[j]) > 0) -> (maximetreMesPeriode[i,j] = (maximeters_powers[i,j]-potenciaOptima[j]) * diesMes[i] * excess_price[j] * 2));

constraint forall(i in 1..nMesos) (((maximeters_powers[i,nPeriodes]-optim_p6) > 0) -> (maximetreMesPeriode[i,nPeriodes] = (maximeters_powers[i,nPeriodes]-optim_p6) * diesMes[i] * excess_price[nPeriodes] * 2));

constraint forall(i in 1..nPeriodes) (totalMaximetres[i] = sum(col(maximetreMesPeriode,i)));
constraint forall(i in 1..(nPeriodes-1)) (totalPotencies[i] = (potenciaOptima[i] * power_price[i]));
constraint totalPotencies[nPeriodes] = optim_p6 * power_price[nPeriodes];

solve minimize totalCost;

output ["'{\"totalCost\": " ++ show(totalCost)];
output [", \"optimalPowers\": ["];
output [show(potenciaOptima[i]) ++ ", " | i in 1..(nPeriodes-1)];
output [show(optim_p6) ++ "]"];
output [", \"totalMaximeters\": " ++ showJSON(totalMaximetres)];
output [", \"totalPowers\": " ++ showJSON(totalPotencies) ++ "}'"];
