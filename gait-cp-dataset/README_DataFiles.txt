GENERAL INFORMATION

G01. Names of file(s) or dataset(s) that this README file describes
	- Kinematics_Kinetics_Baseline.csv
	- Kinematics_Kinetics_Verbal.csv
	- Kinematics_Kinetics_VR.csv
	- Discrete_Parameters_Baseline.csv
	- Discrete_Parameters_Verbal.csv
	- Discrete_Parameters_VR.csv
G02. Date of creation/last update of the README file: 2024-04-30
G03. Name and contact information of Principal Investigator: K. Desloovere, KU Leuven, kaat.desloovere@kuleuven.be
G04. ORCID of Principal Investigator: 0000-0002-8507-5276
G05. Institution of Principal Investigator: KU Leuven
G06. Contact of other person at KU Leuven that has access to the dataset: T. Dewit, tijl.dewit@KULeuven.be
G07. Description of the dataset: The dataset contains kinematic and kinetic parameters as well as discrete gait variables of children with cerebral palsy walking on a treadmill in three conditions: 
	Baseline walking condition, a condition in which verbal feedback on hip extension was given during walking and a condition in which vertual reality feedback on hip extension was given during walking.
G08. Keywords (author defined): Gait, Cerebral palsy, Feedback, Rehabilitation
G09. Thesaurus or controlled vocabulary keywords: Gait
G10. Thesaurus or controlled vocabulary used in this README: none
G11. Language(s) used in the dataset: English
G12. Other involved researchers: G. Molenaers, A. Van Campenhout, K. Desloovere

PROJECT INFORMATION

P01. Project information: /
P02. Project abstract: /
P03. Project funder: /

FILE OVERVIEW

F01. Number of files described by the README-file: 6
F02. List with names of files, description, date of creation of file
	- Kinematics_Kinetics_Baseline.csv, File containing Kinematic and kinetic waveforms of baseline walking condition, 2024-04-30
	- Kinematics_Kinetics_Verbal.csv, File containing Kinematic and kinetic waveforms of verbal feedback walking condition, 2024-04-30
	- Kinematics_Kinetics_VR.csv, File containing Kinematic and kinetic waveforms of virtual reality feedback walking condition, 2024-04-30
	- Discrete_Parameters_Baseline.csv, File containing discrete gait parameters of baseline walking condition, 2024-04-30
	- Discrete_Parameters_Verbal.csv, File containing discrete gait parameters of verbal feedback walking condition, 2024-04-30
	- Discrete_Parameters_VR.csv, File containing discrete gait parameters of virtual reality feedback walking condition, 2024-04-30
F03. File formats: .csv
F04. Software used to generate the data: Vicon Nexus (Vicon, Oxford, UK)
F05. Software necessary to open the file: text editor
F06. Relationship between the files:
	- _Baseline files: Data (kine(ma)tics and discrete gait parameters) of all subjects collected during baseline walking condition
	- _Verbal files: Data (kine(ma)tics and discrete gait parameters) of all subjects collected during verbal feedback walking condition
	- _VR files: Data (kine(ma)tics and discrete gait parameters) of all subjects collected during virtual reality feedback walking condition
F07. Which version of the dataset is this? Date of this version?: V1.0
F08. Information about the dataset versions and reason for updates: NA
F09. Naming conventions for file names: NA

STORAGE INFORMATION

S01. Where are the data stored?: https://doi.org/10.48804/JUNNWW
S02. Links to other available locations of the dataset (e.g. repository): NA

METHODOLOGICAL INFORMATION

M01. Date (beginning-end) and place of data collection: 2018-2022, Clinical Motion Analysis Laboratory, University hospital Leuven, campus Pellenberg
M02. Aim for which the data were collected: Compare affect of Verbal feedback and virtual reality feedback (avatar based) on the gait pattern of children with cerebral palsy
M03. Data collecting method: The dataset was obtained by 3D gait analysis using reflective markers on an instrumented treadmill with embedded forceplates.
M04. Information about data processing methods: All datasets are time-normalized to the gait cycle duration. The amplitude moments are normalized to body weight.
M05. Information about the instrument, calibration: 
	- 3D Motion capture system: Vicon, Oxford, UK (https://www.vicon.com)
	- Treadmill: Gait Real-Time Analysis Interactive Lab (GRAIL) (Motek Medical BV, Amsterdam, The Netherlands)
M06. Quality assurance procedures: Visual data quality check
M07. Information about limitations of the dataset, information that ensures correct interpretation of the dataset: /
M08. People involved in the creation or processing of the dataset
	- H. Adams, T. Dewit

DATA ACCESS AND SHARING

A01. Recommended citation for the dataset: De Mulder, Tine; Adams, Heleen; Dewit, Tijl; Molenaers, Guy; Van Campenhout, Anja; Desloovere, Kaat, 2024, "A Comparison of the Immediate Effects of Verbal and Virtual Reality Feedback on Gait in Children with Cerebral Palsy", https://doi.org/10.48804/JUNNWW, KU Leuven RDR, V1
A02. License information, restrictions on use: CC-BY-NC-SA-4.0
A03. Confidentiality information: NA

DATA SPECIFIC INFORMATION (ABOUT THE DATA THEMSELVES)

D01. Full names and definitions for columns and rows
	- Kinematics_Kinetics files:
		Every row contains data of 1 gait cycle of a subject.
		Column names:
		- subject = anonymized patient code
		- side = measured leg (left or right)
		- weight = subject weight (kg)
		- height = subject height (m)
		- LegLength = length of measured leg (m)
		- aSagP_pct_GC_0 ... aSagP_pct_GC_1000 = sagital pelvis angle (°) during gait cycle
		- aSagH_pct_GC_0 ... aSagH_pct_GC_1000 = sagital hip angle (°) during gait cycle
		- aSagK_pct_GC_0 ... aSagK_pct_GC_1000 = sagital knee angle (°) during gait cycle
		- aSagA_pct_GC_0 ... aSagA_pct_GC_1000 = sagital ankle angle (°) during gait cycle
		- mSagH_pct_GC_0 ... mSagH_pct_GC_1000 = sagital hip moment (Nm/kg) during gait cycle
	- Discrete_Parameters files:
		Every row contains data of 1 gait cycle of a subject.
		Column names:
		- subject = anonymized patient code
		- side = measured leg (left or right)
		- weight = subject weight (kg)
		- height = subject height (m)
		- LegLength = length of measured leg (m)
		- GPS_a = Gait profile score
		- GVS_aSagP = gait variable score for sagital pelvis angle of the gait cycle
		- GVS_aSagH = gait variable score for sagital hip angle of the gait cycle
		- GVS_aSagK = gait variable score for sagital knee angle of the gait cycle
		- GVS_aSagA = gait variable score for sagital ankle angle of the gait cycle
		- aMinSagH = minimal sagital hip angle of the gait cycle
		- pctmZeroStSagH = the timing within the gait cycle at which transition of internal hip extension moment to hip flexion moment occurred
D02. Explanation of abbreviations: see D01.
D03. Units of measurement: kg = kilogram, m = meter, Nm = Newton-meter, ° = angular degree
D04. Symbols for missing data: NaN

RELATIONSHIPS

R01. Publications based on this dataset: De Mulder, T.; Adams, H.; Dewit, T.; Molenaers, G.; Van Campenhout, A.; Desloovere, K. A Comparison of the Immediate Effects of Verbal and Virtual Reality Feedback on Gait in Children with Cerebral Palsy. Children 2024, 11, 524. https://doi.org/10.3390/children11050524 doi: https://doi.org/10.3390/children11050524
R02. This dataset derives from… (other dataset): NA
R03. This dataset is related to… (documents, dataset): NA
R04. References of publications used to create the datasets: NA
