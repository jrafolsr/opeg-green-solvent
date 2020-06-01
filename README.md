# A Tool for the Selection of a Functional Green Solvent

This is the source code generate the web-app  **A Tool for the Selection of a Functional Green Solvent** created by the [Organic Photonics and Electronics group (OPEG)](http://www.opeg-umu.se/). It can be find online [here](http://www.opeg-umu.se/green-solvent-tool).

This app ahas been created using the Python framework [Dash](https://dash.plotly.com/).

### How does it work?

This app helps you to identify functional and environmentally green solvents. The likelihood to be functional is based on Hansen solubility parameters (HSP), where a shorter distance in Hansen space (_Ra_) correspond to a more similar solvent. The greenness or composite score (_G_) is based on the GlaxoSmithKline (GSK) solvent sustainability guide, where a higher G means a greener alternative.

1. Use the radiobuttons on the left panel to either estimate the **HSP coordinates** of your solute from known functional solvent(s) or to manually enter the values. Then click **UPDATE**.

2. The solute is highlighted in the **3D Hansen space**. Use the mouse to explore neighboring solvents. Click on the solvent or select it from the table to find more information.

3. The **Selection table** ranks the solvents based on the distance Ra to your solute, and specifies G.

4. Click **QUICK PATH** to view see a quick testing route towards a green and functional solvent.

5. Use the **Advanced options** to refine your search. Click **UPDATE** to apply your changes.

Find more details in our publication ["A Tool for Identifying Green Solvents for Printed Electronics"](http://www.opeg-umu.se/).