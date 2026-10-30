# Data sources, licences and checksums

All input files are vendored **unchanged** so the notebooks run offline. The Bellinge and treatment-plant notebooks
check their file's SHA-256 before use, and the CI checks every file against the table below. Please cite the
original authors when you reuse the data. Upstream licence texts: [LICENSES/](LICENSES/).

## Netherlands boreholes (`netherlands-boreholes/data/`)

### Pumping tests (`pumping-tests/`)

* **Original source:** Kruseman, G.P. and De Ridder, N.A. (1990). *Analysis and Evaluation of Pumping Test Data*,
  2nd ed. ILRI Publication 47, International Institute for Land Reclamation and Improvement, Wageningen.
  Oude Korendijk (confined aquifer) and Dalem (leaky aquifer) field tests.
* **Digitised files from:** the TTim documentation, https://github.com/mbakker7/ttim, commit
  `e75759040362f010fc0b1a4e74cb20f9b32ee0c1`, folder `docs/03pumpingtests/data/`. Licence: **MIT**, © 2015 mbakker7
  ([LICENSES/ttim-MIT.txt](LICENSES/ttim-MIT.txt)).

| File | SHA-256 |
|---|---|
| `piezometer_h30.txt` | `a705d2fca98d033f840c06604765abbc01014509b30d2d1425626ea50eb3edb5` |
| `piezometer_h90.txt` | `3d31d0f7ac1ff9858a5883e352fc62ccb5d5e4cf4be93333bf36d43f0da4eaa5` |
| `dalem_p30.txt` | `225b44964e677d64432ac17d588c3745d83c26c92c8a1568bd1e2b20a964296e` |
| `dalem_p60.txt` | `b34a9abadec7a2b389210436ffd519262129c8682d4909d4a3bac9f9166069b8` |
| `dalem_p90.txt` | `1960357654fb3e2ba31a827c0ea93fc58c38238374de619859e53d6b1c795b63` |
| `dalem_p120.txt` | `25f6c56854e91aac24d48aeb6ff90b7c4a5edb76dbeb17bb4de2b51bad51b679` |

### Groundwater record, 1960–2015 (`groundwater-record/`)

* **Source:** the Pastas documentation, https://github.com/pastas/pastas, commit
  `76d347e95266bb7722b5c90f7ff80020aa803279`, folder `doc/examples/data_notebook_10/` (observation well with four
  public-supply well fields in the Netherlands). Licence: **MIT**, © 2016-present R.A. Collenteur, M. Bakker, R. Calje,
  F. Schaars ([LICENSES/pastas-MIT.txt](LICENSES/pastas-MIT.txt)).

| File | SHA-256 |
|---|---|
| `Observation_well.csv` | `3caca2ef1885c60323084e59328f5646ac36f15386b6ed29080f0172de68853e` |
| `Precipitation.csv` | `5dcecad5dfe0a5b2fb101bbfc4f2f095e29ac964d2a55dbd83174c389116efd7` |
| `Evaporation.csv` | `e721572b930b4e06f95d9d9ea0c3c145e34d066a91d7343022f961e92cc1a3f9` |
| `Extraction 1.csv` | `d145e8f9880d4a54102ddcdcc1cbf91b229c2631114df87dd2fa6cae014ff396` |
| `Extraction 2.csv` | `a91772e3c5e99b736fb871d30ee8ed5731924228cca78570fd26f6aad2a89916` |
| `Extraction 3.csv` | `55a9d8d84145d7b7d3d7920099374fa1a242360027130287616a17d1b619285a` |
| `Extraction 4.csv` | `6bced7159a66bc66d9eb2bcc85eb72d43060f8353e8deb956c2509636d236466` |

## Denmark: Bellinge sewer network (`denmark-bellinge-sewer/data/`)

* **Source data set:** Nedergaard Pedersen, A., Wied Pedersen, J., Vigueras-Rodriguez, A., Brink-Kjær, A.,
  Borup, M. and Steen Mikkelsen, P. (2021). The Bellinge data set: open data and models for community-wide urban
  drainage systems research. *Earth System Science Data* 13, 4779–4798. https://doi.org/10.5194/essd-13-4779-2021.
  Licence: **CC BY 4.0**.
* **File from:** https://github.com/eWaterCycle/ewatercycle-swmm (repository licence BSD-2-Clause,
  [LICENSES/ewatercycle-swmm-BSD-2-Clause.txt](LICENSES/ewatercycle-swmm-BSD-2-Clause.txt)), commit
  `9dcc535d7888a3c9b38af065575e8a6fb5638021`, `docs/bellinge_example/BellingeSWMM_v021_nopervious.inp`.

| File | SHA-256 |
|---|---|
| `BellingeSWMM_v021_nopervious.inp` | `1ac98b81fbce2a42898423e2cf120ed46d36910637f73ad27c2a1004973c472c` |

Not used: the Bellinge rain-gauge records, which are licensed for non-commercial teaching and research only.

## Treatment plant (`treatment-plant-soft-sensor/data/`)

* **Source:** UCI Machine Learning Repository, *Water Treatment Plant* (dataset 106),
  https://archive.ics.uci.edu/dataset/106/water+treatment+plant. Creator: Manel Poch, Unitat d'Enginyeria Química,
  Universitat Autònoma de Barcelona; donors Javier Béjar and Ulises Cortés, Universitat Politècnica de Catalunya
  (1993). https://doi.org/10.24432/C5FS4C. Licence: **CC BY 4.0**.

| File | SHA-256 |
|---|---|
| `water-treatment.data` | `af2e632b370646ea9763b11aed54b30423f0c3b8a7fb1b7d23e1c922098a7a8a` |

## KAI result files (`*/results/kai_engine_results.json`)

Results produced by the KAI engine (`kai-engine reference …`, October 2026) and published on the KAI platform.
© 2026 KAI Water & Energy, licence **CC BY 4.0**.

## Netherlands: Zeerijp-3A, Groningen Rotliegend (`netherlands-zeerijp-rotliegend/`)

These files are **not vendored**. They are public on [NLOG](https://www.nlog.nl), the Dutch subsurface portal, under
the Mining Act and free to download; the notebooks fetch them on first run into `nlog_cache/` and stop if a SHA-256
differs from the table. Borehole ZEERIJP-03-SIDETRACK1, operator NAM. Please cite *NAM / NLOG* when you reuse them.

| File | NLOG id | SHA-256 |
|---|---|---|
| `ZRP-3A_final_core_analysis.xlsx` (Final Core Analysis data ZRP-3A, 28 Jul 2015) | document 3484333644 | `f362cd8b114573bb6ec6462755190e06b7884ea339330e94df4e9fc69e026049` |
| `mdn_mpd_mai_18aug15_LF1_FRM1.las` (density, neutron, induction, 3490–3872 m) | log document 2085821327 | `66941d92fd7461f49e457029aade0c10b112be5f6419dc3aee636d6f60965ba5` |
| `cxd_18aug15_LF1_FRM1.las` (sonic, 3480–3835 m) | log document 2085820326 | `0250708406f927d299beb03a1c86a5fc9b496231d9483c9c14c4a273e7668794` |

## Spain: Guadalquivir flood triggers (`spain-guadalquivir-flood-triggers/`)

### Derived values in this repository (`data/`)

Each water year's largest daily flow at 14 Guadalquivir gauges and at the matched GloFAS river cell, and the gauge
list, derived by `rebuild_data.py`; each water year's largest catchment rainfall and its October–April total, with the
catchments and rainfall cells behind them, derived by `rebuild_rainfall.py`. Sources below. Licence: **CC BY 4.0**, © 2026 KAI Water & Energy, with
the source credits below.

| File | SHA-256 |
|---|---|
| `annual_maxima.csv` | `4a42889d01e6ed7281eb1ef5388dd32814be5e1a72d0f4ab1bf2d48ec5636011` |
| `gauges.csv` | `10392dea0bf872a2261e910e1b2b0175e69a7bb741e222092fd93578aae14402` |
| `rainfall_maxima.csv` | `40879e973ca4cfc1a8be11ca7d0e9c2366693cbaa9086fa7479d5d5aff675f95` |
| `rain_catchments.csv` | `b18d1c5c0ae93bf220f5c28174b1d8d2ff79373095609fc0399140168721c4db` |
| `rain_cell_weights.csv` | `515efd13b4f61aeccc8874388b21758917434c78285de0db4cd97d48e443201a` |
| `annual_maxima_v5.csv` | `107f994cdbc4b5ffc8952a461506e6b11f85c1cf1cbe85987660c9f40f4ae293` |
| `gauges_v5.csv` | `bec63422e69c992074efc5de83f798ec8433871767324f794a712dbd83882741` |

### Sources (not vendored)

* **CEDEX, *Anuario de Aforos 2021-2022*, Guadalquivir basin** (Spain's Ministry for the Ecological Transition and the
  Demographic Challenge, MITECO), https://ceh-flumen64.cedex.es/anuarioaforos/. The daily files are **not copied
  here**: `rebuild_data.py` downloads them on your own connection (CEDEX refuses some cloud machines) and stops if a
  SHA-256 differs from the table. Please cite *Fuente: CEDEX, Anuario de Aforos 2021-2022 (MITECO)*.

| File | SHA-256 |
|---|---|
| `estaf.csv` (stations: area, position) | `862e812acb71efb1decc1a4ac3b2c5bdd8f66e9a6f8458a9d7f00156cef42ac8` |
| `afliq.csv` (daily mean flow) | `a32995d11447a3b57d642772a14dc046cb5a397ddc5200813d76d39d77ed1ed3` |

* **GloFAS reanalysis**, LISFLOOD, consolidated, version 4.0, Copernicus Emergency Management Service, through the
  Open-Meteo flood API (https://open-meteo.com/en/docs/flood-api; data CC BY 4.0, free API for non-commercial use).
  *Contains modified Copernicus Emergency Management Service information 2026.* GloFAS data are provided for
  information purposes only and are not a flood warning.
* **GloFAS reanalysis**, version 5.0 (consolidated), Copernicus Emergency Management Service, downloaded from the
  Copernicus Early Warning Data Store (dataset `cems-glofas-historical`) for the basin box 38.5 N, 6.45 W to 37.0 N,
  2.65 W, water years 1984-2022 (`annual_maxima_v5.csv`, `gauges_v5.csv`). The 39 yearly netCDF files are not
  vendored; their SHA-256 values are in `glofas_v5_files.sha256`. *Contains modified Copernicus Emergency Management
  Service information 2026 (GloFAS v5.0).* GloFAS data are provided for information purposes only and are not a flood
  warning.
* **NASA POWER** daily precipitation (PRECTOTCORR), https://power.larc.nasa.gov, read through the daily point API.
  *These data were obtained from the NASA Langley Research Center (LaRC) POWER Project funded through the NASA Earth
  Science/Applied Science Program.*
* **HydroBASINS** level 8, Europe (Lehner and Grill, 2013), https://www.hydrosheds.org: catchments for the rainfall.
  Not vendored; only the sub-catchment IDs used are published.

## USA: Utah FORGE geothermal site (`usa-utah-forge-geothermal/data/`)

Derived values only (CC BY 4.0), rebuilt byte for byte by `rebuild_data.py`. *Credit: Utah FORGE, U.S. Department of
Energy, via the Geothermal Data Repository (OpenEI), CC BY 4.0.*

| File | SHA-256 |
|---|---|
| `forge_model.npz` | `8f827f9cad4ea4e5c3ba8b23a948eb2bdbce4f225d74c8f215e94d68f7708d5d` |
| `well_58_32_log_2018.csv` | `0ee61ff2e65573aa2705c108e4ae0e0925b7388e7674f898dc0c1608d359f3cf` |
| `wells.csv` | `9d9cbc26ad0757e5061f64b52ffc5a743db9cfcda22ead24b112f49bef084e77` |
| `fmi_58_32.csv` | `72aa8a3f346a24c92763abee6e0db41df5280fc05b2fb8a7675b07e37908779e` |
| `trajectories_16A_16B.csv` | `3d466ed7ea156655468a5485fb24e8566510cd6bfa61810a449a59ebadcf20a4` |
| `natural_fracture_poles.csv` | `7d65ff422b00ae527dd3516405870175cefc96b91b1eadda4ae6027ac4197a51` |
| `stimulated_dfn.csv` | `adbdc05538a1ecd7a55624ef3eab22460b4a0c025b86316da39c62fdf24ff7fb` |
| `circulation_2024_aug_daily.csv` | `b4cd2afb8fc104e6f772cbea4ed3a5b9faabfb231bc8dc8781898289eada903a` |
| `circulation_2024_summary.json` | `41b5630e709b736ead6c13c795d463ee030ab7c2b30da6c5d2d3a98caad04048` |
| `tracers_2024_circulation.csv` | `cb13beb115a83c97c40de49c77e1b1b31badaac09f171dd62bc26e1680622c11` |
| `dts_16B_2024.csv` | `e8a88483864002e57ae0015cdf96e9e5213a20a188b17abcfc74b77c8cbe33e3` |
| `dts_16B_2024_deep.json` | `e06f2ed3d77c5e4833d7f5ceac741201cfb14bfd8faa0c8014a733013b372ea8` |

### Sources (not vendored; all CC BY 4.0, licence read from each GDR page on 30 Oct 2026)

| File | GDR | SHA-256 |
|---|---|---|
| `Mesh Files.zip` (lithology, 50 m cells) | [1205](https://gdr.openei.org/submissions/1205), DOI 10.15121/1605155 | `ee4b35dffcceb4916d44bc3ac8882e715f154a0f9603d524940aee74a7534704` |
| `Initial Conditions.zip` (temperature, pressure, stress) | [1205](https://gdr.openei.org/submissions/1205), DOI 10.15121/1605155 | `fc29649f321cff916849032c27c949e383709caeddae75b0a501c8334bbf826b` |
| `58-32_Temp_Pres_11_08_18.zip` (58-32 log, 8 Nov 2018) | [1101](https://gdr.openei.org/submissions/1101), DOI 10.15121/1493769 | `04de1f0aebe92e6b3963fcc43f054033d0898cab3d9a238f78d8038ec2826ec8` |
| `Utah FORGE Well and Seismic Locations.csv` (Dec 2021) | [1358](https://gdr.openei.org/submissions/1358) | `7bfc9cf730b8521a71a878ab38381a772ea06821e20f07c06c7ee5e3a5351471` |
| `University_of_Utah_MU-ESW1_FMI-HD_7390-7527ft_Dip Final 3rdRun_Frac_Aps_Only.txt` (58-32 FMI picks) | [1299](https://gdr.openei.org/submissions/1299) | `5bad91b813661bbd51fe7d8083c96ad4a5f85e7702ae218156393716dfbbcb4c` |
| `2024 02A Feb Reference DFN.zip` (trajectories, natural sets) | [1646](https://gdr.openei.org/submissions/1646), DOI 10.15121/2440870 | `107fef6f2c11f6de3f9916ccea5df09d16c21da062126b8644f2464c9d18b809` |
| `2024 05 May New MEQ DFN.zip` (stimulated DFN) | [1646](https://gdr.openei.org/submissions/1646), DOI 10.15121/2440870 | `fe9845773de0054c682b9acdfb25b9c276024a660d80d1803e1785d019d7d095` |
| `Extended Circulation Test.zip` (Aug-Sep 2024) | [1683](https://gdr.openei.org/submissions/1683), DOI 10.15121/2475065 | `ce5a8d4c69ac649024b472219d38601dbd6227ff29cd8c737fe5fe39670786f7` |
| `16A-16B Injection-Circulation.zip` (27 Apr 2024) | [1611](https://gdr.openei.org/submissions/1611), DOI 10.15121/2371032 | `68ee7e43dde01e6aca5f5c205105ce1d7a530e67582e1cc340af00d8842d74cf` |
| `Qpro_tracers.zip` (QuantumPro tracer data, report and slides, 2024) | [1701](https://gdr.openei.org/submissions/1701), DOI 10.15121/2507443 | `4fae497068ccf5185d04576d252355d37515b218ff46ce2e514d420b05caa53b` |
| `Utah Forge 16B(78)-32 - DTS - mmf 2 - evo 4 - part 1.h5` (16B DTS, 4 Aug 2024) | [1721](https://gdr.openei.org/submissions/1721) | `168951d5fda18c25b226707fa32a403bc0e3842ffd14b90431131efe82a40898` |
| `Utah Forge 16B(78)-32 - DTS - mmf 2 - evo 4 - part 2.h5` (16B DTS, 12–16 Aug 2024) | [1721](https://gdr.openei.org/submissions/1721) | `77faaec9d7d10982c215ed233d5477ed5b87892464ea0a89a4c87c4e755eedb7` |
