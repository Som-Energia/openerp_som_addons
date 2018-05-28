# Indexed invoicing for Electra Energía

## PHF formula

 `PHF = (1 + IMU) * [(PMD + POS + [PC3] + OMIE_REE ) * (1 + Perdidas) +  K + D + FONDO_EFICIENCIA ] + PA`

Where:

* **IMU**: Impost Municipal [%]
* **PMD**: Preu Mitjà Diari [€/MWh]
* **POS**: Preu Operació Sistema [€/MWh]
* **PC3]**: Pagos por capacidad según BOE [€/kWh]
* **OMIE_REE**: Retribución OMIE y REE según barras de central [€/MWh]
* **Perdidas**: Perdidas por tarifa [€/MWh]
* **K**: Coeficiente de comercializadora [€/MWh]
* **D**: Desvíos de comercializadora [€/MWh]
* **FONDO_EFICIENCIA**: Pagos al fondo de eficiencia según consumo computado [€/MWh]
* **PA**: Peajes de acceso según BOE [€/kWh]

## Hourly Coeficients

* **PMD +POS +PC**: liquicomun -> prmncur
* **PC**: liquicomun -> prgmncur
* **PMD + POS**: `prmncur - prgmncur`
* **Perdidas**: liquicomun -> Perdxxxxx. xxxxx diferent by tariff

## Pricelist coeficients by period

* **PA**: Peajes (BOE). ERP Module `giscedata_tarifas_peajes_yyyymmdd`
* **PC3**: Pagos por Capacidad (BOE). ERP Module `giscedata_tarifas_pagos_capacidad_yyyymmdd`

## Pricelist coeficients

* **IMU**: Impuesto Municipal. Fixed value by pricelist and version.
* **OMIE_REE**: Retribución OMIE y REE. Fixed value by pricelist and version
* **FONDO_EFICIENCIA**: Pagos Fondo Eficiencia. Fixed value by pricelist and version
* **K**: Margen comercializadora. Fixed value by pricelist and version OR by contract (`coeficiente_k` field)
* **D**: Desvios comercializadora. Fixed value by pricelist and version OR by contract (`coeficiente_d` field)

## audit files

* **phf**: Precio Horario Final (incluye consumo)
* **curve**: Curva 
* **pmd**: prmncur (PMD+POS+PC)
* **pc3_ree**: prgpncur
* **perdues**: perdxxxxx
