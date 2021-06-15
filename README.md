# Green Solvent Selection Tool
[![Green Solvent Tool](https://img.shields.io/badge/web--app-Green%20Solvent%20Tool-brightgreen)](https://green-solvent-tool.herokuapp.com/)
[![OPEG research](https://img.shields.io/badge/research-OPEG-yellow)](http://www.opeg-umu.se/?i=1)
[![MIT license](http://img.shields.io/badge/license-MIT-yellowgreen.svg)](http://opensource.org/licenses/MIT)


This is the source code that generates the web-app  **Green Solvent Selection Tool** created by the [Organic Photonics and Electronics Group (OPEG)](http://www.opeg-umu.se/), which can be found online [here](http://www.opeg-umu.se/green-solvent-tool).

The app helps the user to identify functional and environmentally green solvents. The likelihood to be functional is based on **Hansen solubility parameters** (HSP), where a shorter distance in Hansen space (_Ra_) corresponds to a more similar solvent. The **greenness** or **composite score** (_G_) is based on the GlaxoSmithKline (GSK) solvent sustainability guide, where a higher G means a greener alternative.

This app has been created using the Python framework [Dash](https://dash.plotly.com/).

## How does it work?
1. In the upper left panel, either _enter your known functional solvent(s)_ to approximate the Hansen solubility parameters (HSP), or directly enter the _HSP of your solute_. Click **Update**.

2. The **Solvent Ranking Table** orders the solvents by their distance (Ra) to the solute in the **Hansen space**, i.e. by their similarity in solubility capacity. You can alternatively rank the solvents according to their composite sustainability score (G, a higher value represents a more sustainable alternative), boiling point (bp), viscosity (η), or surface tension (𝜎).

3. By selecting a solvent from the **Hansen space** or the **Solvent Ranking Table** you can get detailed information regarding its chemical structure, physical properties, and sustainability indicators.

4. In the left pane, click **Refinement options** to define the range for G, bp, η, and 𝜎. Click **Update**.

5. Click **Quick path** for a sequential path to greener functional solvents. Starting from your solute, each iteration finds the next nearest solvent with a G higher than the previous.

## Further information
Find more details in our publication ["A Tool for Identifying Green Solvents for Printed Electronics"](http://www.opeg-umu.se/).
