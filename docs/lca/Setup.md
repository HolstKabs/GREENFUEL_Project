# Running the Greenfuel script 

This tool is created to provide executives with research on the theoretical maximum efficiency of different biomass types and their potential environmental impacts on earth. This research is a process of literature study and Life Cycle Assessments on biomass types, when converted with pyrolysis processes to bio-oil for marine transportation

## First step
Compute the biomass type's bio-oil yield, this has been done prior to this script, and it's explained in the section of biomass equilibrium.
The results are saved as an CSV file referred to as yield_results, and they are timestamped to provide the user with the most up-to-date results.

*Reference document(s):"Programming ALI->formulations.md" and "Programming ALI->README".*

## Second step
Locate the bio-oil yield, and calculate the FU which can be done as following:
>**Biomass required to deliver 1 MJ usable bio-oil (kg biomass per 1MJ):**
>
> $m_{bio}$ = $1/(y/100)*HHV$ 
>
> where **y** = bio-oil yield(wt$%), 
>
> **HHV** = Higher Heating Value (of produced bio-oil).

With this equation it's possible to calculate the required amount of biomass to produce 1 MJ of usable bio-oil and thus we can start creating our LCI
*Reference document(s): "LCA_reporting.md".*

## Third step
Categorize the different biomass types, so a broad LCI can be created to accommodate as many different biomass types as possible and different values but still differentiate between yields. This gives the possibility of creating many LCAs of different biomass and but still be somewhat close to reality, when modelling, instead of having to model every single biomass type. This research is trying to provide insights in assumption-based impacts so a very real-world like LCI modelling would be redundant.

*Reference document(s): "biomass_categories.md" and "yield_results_clean.csv".*
## Fourth step
Create dynamic LCI that can look through all computed and categorized biomass types and their corresponding yields, and generate a LCA results that can be interpreted separately. The basis of the LCI will be described in the LCA_reporting and later on there will be a category

*Reference document(s): "Parameters.md", "LCA_reporting.md", "biomass_categories_specific_LCI.md" and "LCI.py".*

## Fifth step

Create csv file with LCA results for interpretation of results. Results should also include four impact categories, always GWP and then for the three other it needs to be the most impactful, either positively or negatively (also shown in the csv file). Set up results so it can be easily transfered to visual representation with for example streamlit web application.

## Sixth step

Export to Streamlit app for webpage 4 - comparing biomass types with yield efficiency, GWP impacts and three other impacts. To be visualized and illustrated for users.