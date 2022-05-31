# Indexed invoicing for SOM Energia

## PHF formula

 `PHF = (1 + IMU) * [(PMD + POS + [PC3] + PC + OMIE_REE ) * (1 + Perdidas) +  K + D + FONDO_EFICIENCIA ] + PA`

Where:

* **IMU**: Impost Municipal [%]
* **PMD**: Preu Mitjà Diari [€/MWh]
* **POS**: Preu Operació Sistema [€/MWh]
* **PC3]**: Pagos por capacidad según BOE [€/kWh]
* **OMIE_REE**: Retribución OMIE y REE según barras de central [€/MWh]
* **Perdidas**: Perdidas por tarifa [%]
* **K**: Coeficiente de comercializadora [€/kWh]
* **D**: Desvíos de comercializadora [€/kWh]
* **FONDO_EFICIENCIA**: Pagos al fondo de eficiencia según consumo computado [€/MWh]
* **PA**: Peajes de acceso según BOE [€/kWh]

### Hourly Coeficients

* **PMD +POS +PC**: liquicomun -> prmncur
* **PC**: liquicomun -> prgpncur
* **PMD + POS**: `prmncur - prgpncur`
* **Perdidas**: liquicomun -> Perdxxxxx. xxxxx diferent by tariff

### Pricelist coeficients by period

* **PA**: Peajes (BOE). ERP Module `giscedata_tarifas_peajes_yyyymmdd`
* **PC3**: Pagos por Capacidad (BOE). ERP Module `giscedata_tarifas_pagos_capacidad_yyyymmdd`

### Pricelist coeficients

* **IMU**: Impuesto Municipal. Fixed value by pricelist and version.
* **OMIE_REE**: Retribución OMIE y REE. Fixed value by pricelist and version
* **FONDO_EFICIENCIA**: Pagos Fondo Eficiencia. Fixed value by pricelist and version
* **K**: Margen comercializadora. Fixed value by pricelist and version OR by contract (`coeficiente_k` field)
* **D**: Desvios comercializadora. Fixed value by pricelist and version OR by contract (`coeficiente_d` field)

### audit files

* **phf**: Precio Horario Final (incluye consumo)
* **curve**: Curva 
* **pmd**: prmncur (PMD+POS+PC)
* **pc3_ree**: prgpncur
* **perdues**: perdxxxxx

## PHF PENINSULA formula

 `PHF = (1 + IMU) * [(PMD + PC + POS + OMIE_REE + H) * (1 + Perdidas) + FNEE + K + D] + PA`

Where:

* **IMU**: Impost Municipal [%]
* **PMD**: Preu Mitjà Diari [€/MWh]
* **PC**: Pagos por capacidad según BOE [€/kWh]
* **POS**: Preu Operació Sistema [€/MWh]
* **OMIE_REE**: Retribución OMIE y REE según barras de central [€/MWh]
* **H**: Coeficiente de comercializadora [€/kWh]
* **Perdidas**: Perdidas por tarifa [%]
* **FNEE**: Pagos al fondo de eficiencia según consumo computado [€/MWh]
* **K**: Coeficiente de comercializadora [€/kWh]
* **D**: Desvíos de comercializadora [€/kWh]
* **PA**: Peajes de acceso según BOE [€/kWh]

### Hourly Coeficients

* **PMD**: liquicomun -> prmdiari
* **Perdidas**: liquicomun -> Perdxxxxx. xxxxx diferent by tariff

### Pricelist coeficients by period

* **PA**: Peajes (BOE). ERP Module `giscedata_tarifas_peajes_yyyymmdd`
* **PC**: Pagos por Capacidad (BOE). ERP Module `giscedata_tarifas_pagos_capacidad_yyyymmdd`

### Pricelist coeficients

* **IMU**: Impuesto Municipal. Fixed value by pricelist and version.
* **OMIE_REE**: Retribución OMIE y REE. Fixed value by pricelist and version
* **FNEE**: Pagos Fondo Eficiencia. Fixed value by pricelist and version
* **K**: Margen comercializadora. Fixed value by pricelist and version OR by contract (`coeficient_k` field)
* **D**: Desvios comercializadora. Fixed value by pricelist and version OR by contract (`coeficient_d` field)

### Contract coefficients

* **H**: Margen comercializadora. Fixed value by contract (`coeficient_h` field)

### audit files

* **phf**: Precio Horario Final (incluye consumo)
* **curve**: Curva
* **pmd**: prmdiari
* **perdues**: perdxxxxx

## PHF BALEARES formula

 `PHF = (1 + IMU) * [(SPHDEM + PC_REE + SI + POS) * (1 + Perdidas) + FNEE + K] + PA + CA`

Where:

* **IMU**: Impost Municipal [%]
* **SPHDEM**:  Precio Medio de Demanda en los sistemas no peninsulares [€/MWh]
* **PC_REE**: Pagos por capacidad según REE [€/kWh]
* **SI**: Precio Servicio Interrumpibilidad [€/MWh]
* **POS**: Preu Operació Sistema [€/MWh]
* **Perdidas**: Perdidas por tarifa [%]
* **FNEE**: Pagos al fondo de eficiencia según consumo computado [€/MWh]
* **K**: Coeficiente de comercializadora [€/kWh]
* **PA**: Peajes de acceso según BOE [€/kWh]
* **CA**: Cargos según BOE [€/kWh]

### Hourly Coeficients

* **SPHDEM**: liquicomun -> sphdem
* **Perdidas**: liquicomun -> Sperdxxxxx. xxxxx diferent by tariff

### Pricelist coeficients by period

* **PA**: Peajes (BOE). ERP Module `giscedata_tarifas_peajes_yyyymmdd`
* **CA**: Cargos (BOE). ERP Module `giscedata_tarifas_cargos_yyyymmdd`

### Pricelist coeficients

* **IMU**: Impuesto Municipal. Fixed value by pricelist and version.
* **FNEE**: Pagos Fondo Eficiencia. Fixed value by pricelist and version
* **K**: Margen comercializadora. Fixed value by pricelist and version OR by contract (`coeficient_k` field)

### audit files

* **phf**: Precio Horario Final (incluye consumo)
* **curve**: Curva
* **pmd**: sphdem
* **perdues**: perdxxxxx

## PHF BALEARES formula

 `PHF = (1 + IMU) * [(SPHDEM + PC_REE + SI + POS) * (1 + Perdidas) + FNEE + K] + PA + CA`

Where:

* **IMU**: Impost Municipal [%]
* **SPHDEM**:  Precio Medio de Demanda en los sistemas no peninsulares [€/MWh]
* **PC_REE**: Pagos por capacidad según REE [€/kWh]
* **SI**: Precio Servicio Interrumpibilidad [€/MWh]
* **POS**: Preu Operació Sistema [€/MWh]
* **Perdidas**: Perdidas por tarifa [%]
* **FNEE**: Pagos al fondo de eficiencia según consumo computado [€/MWh]
* **K**: Coeficiente de comercializadora [€/kWh]
* **PA**: Peajes de acceso según BOE [€/kWh]
* **CA**: Cargos según BOE [€/kWh]

### Hourly Coeficients

* **SPHDEM**: liquicomun -> sphdem
* **Perdidas**: liquicomun -> Sperdxxxxx. xxxxx diferent by tariff

### Pricelist coeficients by period

* **PA**: Peajes (BOE). ERP Module `giscedata_tarifas_peajes_yyyymmdd`
* **CA**: Cargos (BOE). ERP Module `giscedata_tarifas_cargos_yyyymmdd`

### Pricelist coeficients

* **IMU**: Impuesto Municipal. Fixed value by pricelist and version.
* **FNEE**: Pagos Fondo Eficiencia. Fixed value by pricelist and version
* **K**: Margen comercializadora. Fixed value by pricelist and version OR by contract (`coeficient_k` field)

### audit files

* **phf**: Precio Horario Final (incluye consumo)
* **curve**: Curva
* **pmd**: sphdem
* **perdues**: perdxxxxx

## PHF Generació

 `PHF = [PMD]`

### Hourly Coeficients

* **PMD**: liquicomun -> prmdiari

### audit files

* **pvpc_gen**: prmdiari
* **curve_gen**: Curva
* **phf_gen**: Precio Horario Final (incluye consumo)
