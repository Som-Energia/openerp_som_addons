<%def name="summary_legal(features, bono_social_estimate)">
<div class="summary-box">
    <h3>6. Duración y prórroga del contrato</h3>
    <div class="summary-content">
        <p class="section-text">La duración del contrato es trimestral natural.</p>
        <p class="section-text">Vencido cada período trimestral natural, el contrato se prorrogará tácita y automáticamente por períodos trimestrales naturales sucesivos, salvo que alguna de las partes comunique su voluntad de no prorrogar.</p>
        <p class="section-text">En caso de que SOM ENERGIA, SCCL te comunique una modificación sustancial del contrato o una revisión del precio aplicable, podrás resolver el contrato sin penalización en el plazo de 15 días naturales.</p>
        %if features['show_section_6_final_paragraph']:
            <p class="section-text">En caso de que tengas contratado el Servicio GURB, anualmente se actualizará la cuota GURB según el Índice de Precios al Consumo.</p>
        %endif
    </div>
</div>

<div class="summary-box">
    <h3>7. Resolución y penalizaciones</h3>
    <div class="summary-content">
        <p class="section-text">Puedes rescindir tu contrato y sus prórrogas en cualquier momento sin perjuicio de las obligaciones de pago por consumos efectivamente realizados y, en su caso, de los costes que legalmente procedan.</p>
        %if features['show_section_7_final_paragraph']:
            <p class="section-text">En caso de que tengas contratado el Servicio GURB o la tarifa Generation kWh, si resuelves el contrato de suministro con tarifa períodos y/o indexada dará lugar a la baja automática del Servicio GURB o tarifa Generation kWh.</p>
        %endif
    </div>
</div>

<div class="summary-box">
    <h3>8. Derecho de desistimiento</h3>
    <div class="summary-content">
        <p class="section-text">Siempre que tengas la condición de consumidora podrá desistir del presente contrato sin necesidad de alegar causa alguna, dentro del plazo de catorce (14) días naturales desde su celebración.</p>
    </div>
</div>

<div class="summary-box">
    <h3>9. Información relevante sobre la tarifa Indexada</h3>
    <div class="summary-content">
        <p class="section-text">El precio es diferente cada cuarto de hora y puede aumentar en periodos de alta demanda, escasa aportación renovable y/o encarecimiento de la producción con combustibles fósiles.</p>
        <p class="section-text">Puedes ahorrar costes adaptando el consumo a los períodos más económicos y consultar la tendencia de precios en la web de Som Energia.</p>
    </div>
</div>

</%def>
