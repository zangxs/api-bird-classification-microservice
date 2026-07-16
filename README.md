# api-bird-classification-microservice

Microservicio Python (sin API HTTP, solo consumer) encargado de clasificar la especie de un ave a
partir de una imagen ya confirmada como "ave" por `api-bird-detection-microservice`. Forma parte
del workspace `bird-dex`.

## Qué hace

1. Consume mensajes de la cola `bird_classification.queue` (exchange `bird_detection.exchange`).
2. Descarga la imagen desde S3 usando el `s3Key` del mensaje.
3. Corre un modelo fastai (`app/ml/bird_species_classifier_latest.pkl`) para predecir la especie.
4. Publica el resultado (`scientificName`, `specieConfidence`, `failureReason`, `alternatives`) con
   la routing key `bird_classification.result` en el mismo exchange.

Si la confianza de la predicción es menor a `CONFIDENCE_THRESHOLD` (0.70, en
`app/service/bird_classification_service.py`), se publica el resultado con `failureReason =
"LOW_CONFIDENCE"` y `scientificName` vacío.

Además del resultado principal, el servicio calcula hasta `TOP_K` (3) especies alternativas: de las
top-3 predicciones del modelo, se excluye la predicción principal y se descartan las que tengan una
confianza menor a `top1_confidence - AMBIGUITY_MARGIN` (0.15). El resultado es la lista
`alternatives`, cada entrada con `scientificName` y `specieConfidence` — puede ir vacía si no hay
especies suficientemente cercanas a la predicción principal. Esto se calcula siempre, incluso cuando
la clasificación principal tiene éxito (no solo en `LOW_CONFIDENCE`).

## Requisitos

- Python 3.12
- Una instancia de RabbitMQ accesible (misma que usan el orquestador y el servicio de detección)
- Credenciales de AWS S3 con acceso al bucket donde se suben las imágenes

### Modelo requerido

El servicio necesita el archivo de modelo en `app/ml/bird_species_classifier_latest.pkl`. Es data
gitignoreada (85–100MB+), no viene en el repo.

**Descarga desde Hugging Face** (público, sin token):

```bash
mkdir -p app/ml
curl -L -o app/ml/bird_species_classifier_latest.pkl \
  https://huggingface.co/brayanspv/bird_classification/resolve/main/bird_species_classifier_latest.pkl

# verifica que el archivo descargado sea exactamente el que se subió
echo "4b93c63d3a9d77b08da0e762c5560eeadcef4cf559947f8889d08680c532782d  app/ml/bird_species_classifier_latest.pkl" | sha256sum -c
```

Repo: <https://huggingface.co/brayanspv/bird_classification/tree/main>. Sin el archivo, el proceso
falla al iniciar en `load_learner(...)` — es la señal esperada, no un bug.

## Instalación

```bash
python -m venv env
source env/bin/activate
pip install -r requirements.txt
```

## Configuración

Variables de entorno (ver `app/config/config.py`), definidas en un archivo `.env` en la raíz del
repo (**nunca commitear este archivo, contiene credenciales reales**):

| Variable | Descripción | Default |
|---|---|---|
| `RABBITMQ_URL` | URL de conexión a RabbitMQ | `amqp://user:password@localhost:5672/` |
| `QUEUE_CLASSIFICATION_NAME` | Cola de entrada | `bird_classification.queue` |
| `EXCHANGE_NAME` | Exchange compartido con el resto de servicios | `bird_detection.exchange` |
| `RESULT_ROUTING_KEY` | Routing key para publicar el resultado | `bird_classification.result` |
| `S3_BUCKET` | Bucket donde están las imágenes (requerido) | — |
| `AWS_ACCESS_KEY_ID` | Access key de AWS (requerido) | — |
| `AWS_SECRET_ACCESS_KEY` | Secret key de AWS (requerido) | — |
| `AWS_REGION` | Región de S3 | `us-east-1` |

## Cómo correrlo

```bash
source env/bin/activate
python -m app.main
```

Esto valida la configuración, se conecta a RabbitMQ, arranca el consumer sobre
`bird_classification.queue` y queda escuchando mensajes indefinidamente (no imprime nada más si no
llegan mensajes; eso es esperado). Deténlo con `Ctrl+C`.

No hay servidor HTTP en este repo — es un proceso consumer puro. Sí hay `Dockerfile` (ver
`../DOCKER.md` en la raíz del workspace para levantarlo junto con el resto de servicios vía
`docker compose`); el modelo se monta como volumen en tiempo de ejecución, no se descarga durante
el build.

## Especies que puede clasificar

El vocabulario del modelo (`app/ml/bird_species_classifier_latest.pkl`) tiene 500 especies —
principalmente avifauna de Colombia, dado el dataset de entrenamiento (ver
`bird-classification-notebook`). El nombre devuelto en `scientificName` es el nombre científico
tal como aparece en esta lista (con espacio en vez de guión bajo).

<details>
<summary>Ver las 500 especies (nombre común / nombre científico)</summary>

| Nombre común | Nombre científico |
|---|---|
| Acadian Flycatcher | *Empidonax virescens* |
| Acorn Woodpecker | *Melanerpes formicivorus* |
| Amazon Kingfisher | *Chloroceryle amazona* |
| American Barn Owl | *Tyto furcata* |
| American Coot | *Fulica americana* |
| American Flamingo | *Phoenicopterus ruber* |
| American Kestrel | *Falco sparverius* |
| American Redstart | *Setophaga ruticilla* |
| Andean Cock-of-the-rock | *Rupicola peruvianus* |
| Andean Condor | *Vultur gryphus* |
| Andean Duck | *Oxyura ferruginea* |
| Andean Emerald | *Uranomitra franciae* |
| Andean Guan | *Penelope montagnii* |
| Andean Motmot | *Momotus aequatorialis* |
| Andean Siskin | *Spinus spinescens* |
| Andean Solitaire | *Myadestes ralloides* |
| Andean Teal | *Anas andium* |
| Anhinga | *Anhinga anhinga* |
| Apical Flycatcher | *Myiarchus apicalis* |
| Aplomado Falcon | *Falco femoralis* |
| Azara's Spinetail | *Synallaxis azarae* |
| Baltimore Oriole | *Icterus galbula* |
| Bananaquit | *Coereba flaveola* |
| Band-backed Wren | *Campylorhynchus zonatus* |
| Band-tailed Guan | *Penelope argyrotis* |
| Band-tailed Pigeon | *Patagioenas fasciata* |
| Band-winged Nightjar | *Systellura longirostris* |
| Bar-crested Antshrike | *Thamnophilus multistriatus* |
| Bare-faced Ibis | *Phimosus infuscatus* |
| Barn Swallow | *Hirundo rustica* |
| Barred Antshrike | *Thamnophilus doliatus* |
| Bat Falcon | *Falco rufigularis* |
| Bay-breasted Warbler | *Setophaga castanea* |
| Bay-headed Tanager | *Tangara gyrola* |
| Beautiful Woodpecker | *Melanerpes pulcher* |
| Beryl-spangled Tanager | *Tangara nigroviridis* |
| Bicolored Wren | *Campylorhynchus griseus* |
| Black Flowerpiercer | *Diglossa humeralis* |
| Black Hawk-Eagle | *Spizaetus tyrannus* |
| Black Inca | *Coeligena prunellei* |
| Black Phoebe | *Sayornis nigricans* |
| Black Skimmer | *Rynchops niger* |
| Black Vulture | *Coragyps atratus* |
| Black-and-chestnut Eagle | *Spizaetus isidori* |
| Black-and-gold Tanager | *Bangsia melanochlamys* |
| Black-and-white Warbler | *Mniotilta varia* |
| Black-backed Grosbeak | *Pheucticus aureoventris* |
| Black-bellied Whistling-Duck | *Dendrocygna autumnalis* |
| Black-billed Mountain-Toucan | *Andigena nigrirostris* |
| Black-billed Thrush | *Turdus ignobilis* |
| Black-capped Donacobius | *Donacobius atricapilla* |
| Black-capped Tanager | *Stilpnia heinei* |
| Black-cheeked Woodpecker | *Melanerpes pucherani* |
| Black-chested Buzzard-Eagle | *Geranoaetus melanoleucus* |
| Black-chested Jay | *Cyanocorax affinis* |
| Black-collared Hawk | *Busarellus nigricollis* |
| Black-collared Jay | *Cyanolyca armillata* |
| Black-crested Antshrike | *Sakesphorus canadensis* |
| Black-crested Warbler | *Myiothlypis nigrocristata* |
| Black-crowned Antshrike | *Thamnophilus atrinucha* |
| Black-crowned Night Heron | *Nycticorax nycticorax* |
| Black-crowned Tityra | *Tityra inquisitor* |
| Black-faced Grassquit | *Melanospiza bicolor* |
| Black-faced Tanager | *Schistochlamys melanopis* |
| Black-fronted Nunbird | *Monasa nigrifrons* |
| Black-headed Tanager | *Stilpnia cyanoptera* |
| Black-necked Stilt | *Himantopus mexicanus* |
| Black-striped Sparrow | *Arremonops conirostris* |
| Black-tailed Tityra | *Tityra cayana* |
| Black-tailed Trainbearer | *Lesbia victoriae* |
| Black-throated Mango | *Anthracothorax nigricollis* |
| Black-winged Saltator | *Saltator atripennis* |
| Blackburnian Warbler | *Setophaga fusca* |
| Blue Dacnis | *Dacnis cayana* |
| Blue-and-black Tanager | *Tangara vassorii* |
| Blue-and-white Swallow | *Pygochelidon cyanoleuca* |
| Blue-and-yellow Macaw | *Ara ararauna* |
| Blue-billed Curassow | *Crax alberti* |
| Blue-black Grassquit | *Volatinia jacarina* |
| Blue-capped Tanager | *Sporathraupis cyanocephala* |
| Blue-gray Tanager | *Thraupis episcopus* |
| Blue-headed Parrot | *Pionus menstruus* |
| Blue-naped Chlorophonia | *Chlorophonia cyanea* |
| Blue-necked Tanager | *Stilpnia cyanicollis* |
| Blue-throated Starfrontlet | *Coeligena helianthea* |
| Blue-winged Mountain-Tanager | *Anisognathus somptuosus* |
| Blue-winged Teal | *Spatula discors* |
| Bluish Flowerpiercer | *Diglossa caerulescens* |
| Boat-billed Flycatcher | *Megarynchus pitangua* |
| Bogotá Rail | *Rallus semiplumbeus* |
| Broad-winged Hawk | *Buteo platypterus* |
| Bronze-winged Parrot | *Pionus chalcopterus* |
| Bronzy Inca | *Coeligena coeligena* |
| Brown Jacamar | *Brachygalba lugubris* |
| Brown Pelican | *Pelecanus occidentalis* |
| Brown Violetear | *Colibri delphinae* |
| Brown-backed Chat-Tyrant | *Ochthoeca fumicolor* |
| Brown-bellied Swallow | *Orochelidon murina* |
| Brown-capped Vireo | *Vireo leucophrys* |
| Brown-throated Parakeet | *Eupsittula pertinax* |
| Buff-necked Ibis | *Theristicus caudatus* |
| Buff-rumped Warbler | *Myiothlypis fulvicauda* |
| Buff-tailed Coronet | *Boissonneaua flavescens* |
| Buff-throated Saltator | *Saltator maximus* |
| Buff-winged Starfrontlet | *Coeligena lutetiae* |
| Buffy Helmetcrest | *Oxypogon stuebelii* |
| Burnished-buff Tanager | *Stilpnia cayana* |
| Burrowing Owl | *Athene cunicularia* |
| Canada Warbler | *Cardellina canadensis* |
| Capped Heron | *Pilherodius pileatus* |
| Carib Grackle | *Quiscalus lugubris* |
| Caribbean Hornero | *Furnarius longirostris* |
| Cattle Tyrant | *Machetornis rixosa* |
| Cauca Guan | *Penelope perspicax* |
| Channel-billed Toucan | *Ramphastos vitellinus* |
| Chestnut Wood-Quail | *Odontophorus hyperythrus* |
| Chestnut-bellied Chat-Tyrant | *Ochthoeca cinnamomeiventris* |
| Chestnut-capped Brushfinch | *Arremon brunneinucha* |
| Chestnut-capped Warbler | *Basileuterus delattrii* |
| Chestnut-crowned Antpitta | *Grallaria ruficapilla* |
| Chestnut-eared Aracari | *Pteroglossus castanotis* |
| Chestnut-fronted Macaw | *Ara severus* |
| Chestnut-headed Oropendola | *Psarocolius wagleri* |
| Chestnut-winged Chachalaca | *Ortalis garrula* |
| Chocó Brushfinch | *Atlapetes crassus* |
| Cinereous Becard | *Pachyramphus rufus* |
| Cinnamon Becard | *Pachyramphus cinnamomeus* |
| Cinnamon Flycatcher | *Pyrrhomyias cinnamomeus* |
| Clay-colored Thrush | *Turdus grayi* |
| Cocoi Heron | *Ardea cocoi* |
| Collared Aracari | *Pteroglossus torquatus* |
| Collared Inca | *Coeligena torquata* |
| Collared Trogon | *Trogon collaris* |
| Colombian Chachalaca | *Ortalis columbiana* |
| Common Black Hawk | *Buteogallus anthracinus* |
| Common Chlorospingus | *Chlorospingus flavopectus* |
| Common Gallinule | *Gallinula galeata* |
| Common Ground Dove | *Columbina passerina* |
| Common Pauraque | *Nyctidromus albicollis* |
| Common Potoo | *Nyctibius griseus* |
| Common Squirrel-Cuckoo | *Piaya cayana* |
| Common Tody-Flycatcher | *Todirostrum cinereum* |
| Crested Ant-Tanager | *Driophlox cristata* |
| Crested Bobwhite | *Colinus cristatus* |
| Crested Caracara | *Caracara plancus* |
| Crested Oropendola | *Psarocolius decumanus* |
| Crestless Curassow | *Mitu tomentosum* |
| Crimson-backed Tanager | *Ramphocelus dimidiatus* |
| Crimson-crested Woodpecker | *Campephilus melanoleucos* |
| Crimson-mantled Woodpecker | *Colaptes rivolii* |
| Crimson-rumped Toucanet | *Aulacorhynchus haematopygus* |
| Crowned Woodnymph | *Thalurania colombica* |
| Double-striped Thick-knee | *Hesperoburhinus bistriatus* |
| Eared Dove | *Zenaida auriculata* |
| Eastern Kingbird | *Tyrannus tyrannus* |
| Eastern Meadowlark | *Sturnella magna* |
| Eastern Wood-Pewee | *Contopus virens* |
| Empress Brilliant | *Heliodoxa imperatrix* |
| Fasciated Tiger-Heron | *Tigrisoma fasciatum* |
| Fawn-breasted Brilliant | *Heliodoxa rubinoides* |
| Fawn-breasted Tanager | *Pipraeidea melanonota* |
| Ferruginous Pygmy-Owl | *Glaucidium brasilianum* |
| Flame-faced Tanager | *Tangara parzudakii* |
| Flame-rumped Tanager | *Ramphocelus flammigerus* |
| Fork-tailed Flycatcher | *Tyrannus savana* |
| Fulvous Whistling-Duck | *Dendrocygna bicolor* |
| Gartered Violaceous Trogon | *Trogon caligatus* |
| Giant Cowbird | *Molothrus oryzivorus* |
| Glaucous Tanager | *Thraupis glaucocolpa* |
| Glittering-throated Emerald | *Chionomesa fimbriata* |
| Glossy Flowerpiercer | *Diglossa lafresnayii* |
| Glossy Ibis | *Plegadis falcinellus* |
| Glowing Puffleg | *Eriocnemis vestita* |
| Gold-ringed Tanager | *Bangsia aureocincta* |
| Golden Tanager | *Tangara arthus* |
| Golden-bellied Flycatcher | *Myiodynastes hemichrysus* |
| Golden-bellied Starfrontlet | *Coeligena bonapartei* |
| Golden-collared Manakin | *Manacus vitellinus* |
| Golden-crowned Warbler | *Basileuterus culicivorus* |
| Golden-faced Tyrannulet | *Zimmerius chrysops* |
| Golden-fronted Redstart | *Myioborus ornatus* |
| Golden-headed Manakin | *Ceratopipra erythrocephala* |
| Golden-headed Quetzal | *Pharomachrus auriceps* |
| Golden-hooded Tanager | *Stilpnia larvata* |
| Golden-naped Tanager | *Chalcothraupis ruficervix* |
| Golden-olive Woodpecker | *Colaptes rubiginosus* |
| Golden-rumped Euphonia | *Chlorophonia cyanocephala* |
| Grass Wren | *Cistothorus platensis* |
| Grass-green Tanager | *Chlorornis riefferii* |
| Grassland Yellow-Finch | *Sicalis luteola* |
| Gray Kingbird | *Tyrannus dominicensis* |
| Gray Seedeater | *Sporophila intermedia* |
| Gray-breasted Martin | *Progne chalybea* |
| Gray-breasted Mountain-Toucan | *Andigena hypoglauca* |
| Gray-breasted Wood-Wren | *Henicorhina leucophrys* |
| Gray-browed Brushfinch | *Arremon assimilis* |
| Gray-cowled Wood-Rail | *Aramides cajaneus* |
| Gray-headed Tanager | *Eucometis penicillata* |
| Gray-lined Hawk | *Buteo nitidus* |
| Grayish Piculet | *Picumnus granadensis* |
| Great Egret | *Ardea alba* |
| Great Kiskadee | *Pitangus sulphuratus* |
| Great Potoo | *Nyctibius grandis* |
| Great Sapphirewing | *Pterophanes cyanopterus* |
| Great Thrush | *Turdus fuscater* |
| Great-tailed Grackle | *Quiscalus mexicanus* |
| Greater Ani | *Crotophaga major* |
| Greater Yellowlegs | *Tringa melanoleuca* |
| Green Hermit | *Phaethornis guy* |
| Green Heron | *Butorides virescens* |
| Green Honeycreeper | *Chlorophanes spiza* |
| Green Ibis | *Mesembrinibis cayennensis* |
| Green Jay | *Cyanocorax yncas* |
| Green Kingfisher | *Chloroceryle americana* |
| Green Thorntail | *Discosura conversii* |
| Green-and-black Fruiteater | *Pipreola riefferii* |
| Green-backed Trogon | *Trogon viridis* |
| Green-crowned Brilliant | *Heliodoxa jacula* |
| Green-tailed Trainbearer | *Lesbia nuna* |
| Greenish Puffleg | *Haplophaedia aureliae* |
| Greylag Goose | *Anser anser* |
| Groove-billed Ani | *Crotophaga sulcirostris* |
| Guira Tanager | *Hemithraupis guira* |
| Helmeted Guineafowl | *Numida meleagris* |
| Hepatic Tanager | *Piranga flava* |
| Hoatzin | *Opisthocomus hoazin* |
| Hooded Mountain-Tanager | *Buthraupis montana* |
| Hook-billed Kite | *Chondrohierax uncinatus* |
| Horned Screamer | *Anhima cornuta* |
| Hudsonian Whimbrel | *Numenius hudsonicus* |
| Indigo-capped Hummingbird | *Saucerottia cyanifrons* |
| Jabiru | *Jabiru mycteria* |
| Keel-billed Toucan | *Ramphastos sulfuratus* |
| King Vulture | *Sarcoramphus papa* |
| Lacrimose Mountain-Tanager | *Anisognathus lacrymosus* |
| Lance-tailed Manakin | *Chiroxiphia lanceolata* |
| Large-billed Tern | *Phaetusa simplex* |
| Laughing Falcon | *Herpetotheres cachinnans* |
| Laughing Gull | *Leucophaeus atricilla* |
| Least Grebe | *Tachybaptus dominicus* |
| Least Sandpiper | *Calidris minutilla* |
| Lesser Goldfinch | *Spinus psaltria* |
| Lesser Kiskadee | *Philohydor lictor* |
| Lesser Violetear | *Colibri cyanotus* |
| Lesser Yellow-headed Vulture | *Cathartes burrovianus* |
| Lesser Yellowlegs | *Tringa flavipes* |
| Lettered Aracari | *Pteroglossus inscriptus* |
| Limpkin | *Aramus guarauna* |
| Lineated Woodpecker | *Dryocopus lineatus* |
| Little Blue Heron | *Egretta caerulea* |
| Little Tinamou | *Crypturellus soui* |
| Long-tailed Sylph | *Aglaiocercus kingii* |
| Long-tailed Tyrant | *Colonia colonus* |
| Longuemare's Sunangel | *Heliangelus clarisse* |
| Magnificent Frigatebird | *Fregata magnificens* |
| Magpie Tanager | *Cissopis leverianus* |
| Mallard | *Anas platyrhynchos* |
| Mallard × Muscovy Duck | *Anas platyrhynchos × Cairina moschata* |
| Masked Cardinal | *Paroaria nigrogenis* |
| Masked Flowerpiercer | *Diglossa cyanea* |
| Masked Tityra | *Tityra semifasciata* |
| Masked Trogon | *Trogon personatus* |
| Merlin | *Falco columbarius* |
| Metallic-green Tanager | *Tangara labradorides* |
| Montane Woodcreeper | *Lepidocolaptes lacrymiger* |
| Mountain Cacique | *Cacicus chrysonotus* |
| Mountain Elaenia | *Elaenia frantzii* |
| Mountain Velvetbreast | *Lafresnaya lafresnayi* |
| Mountain Wren | *Troglodytes solstitialis* |
| Mourning Warbler | *Geothlypis philadelphia* |
| Moustached Brushfinch | *Atlapetes albofrenatus* |
| Moustached Puffbird | *Malacoptila mystacalis* |
| Multicolored Tanager | *Chlorochrysa nitidissima* |
| Muscovy Duck | *Cairina moschata* |
| Neotropic Cormorant | *Nannopterum brasilianum* |
| Northern Screamer | *Chauna chavaria* |
| Northern Slaty Brushfinch | *Atlapetes schistaceus* |
| Northern Waterthrush | *Parkesia noveboracensis* |
| Northern White-fringed Antwren | *Formicivora intermedia* |
| Northern Yellow Warbler | *Setophaga aestiva* |
| Ochre-bellied Flycatcher | *Mionectes oleagineus* |
| Oilbird | *Steatornis caripensis* |
| Olivaceous Piculet | *Picumnus olivaceus* |
| Olive-gray Saltator | *Saltator olivascens* |
| Olive-sided Flycatcher | *Contopus cooperi* |
| Orange-bellied Euphonia | *Euphonia xanthogaster* |
| Orange-chinned Parakeet | *Brotogeris jugularis* |
| Orange-crowned Oriole | *Icterus auricapillus* |
| Orange-winged Amazon | *Amazona amazonica* |
| Orinoco Goose | *Oressochen jubatus* |
| Oriole Blackbird | *Gymnomystax mexicanus* |
| Ornate Flycatcher | *Myiotriccus ornatus* |
| Osprey | *Pandion haliaetus* |
| Pale-breasted Spinetail | *Synallaxis albescens* |
| Pale-breasted Thrush | *Turdus leucomelas* |
| Pale-edged Flycatcher | *Myiarchus cephalotes* |
| Pale-naped Brushfinch | *Atlapetes pallidinucha* |
| Pale-vented Pigeon | *Patagioenas cayennensis* |
| Palm Tanager | *Thraupis palmarum* |
| Pearl Kite | *Gampsonyx swainsonii* |
| Pearled Treerunner | *Margarornis squamiger* |
| Pied Puffbird | *Notharchus tectus* |
| Pied Water-Tyrant | *Fluvicola pica* |
| Pied-billed Grebe | *Podilymbus podiceps* |
| Pileated Finch | *Coryphospingus pileatus* |
| Piratic Flycatcher | *Legatus leucophaius* |
| Plain Antvireo | *Dysithamnus mentalis* |
| Plain-brown Woodcreeper | *Dendrocincla fuliginosa* |
| Plain-colored Seedeater | *Catamenia inornata* |
| Plain-colored Tanager | *Tangara inornata* |
| Plumbeous Kite | *Ictinia plumbea* |
| Plumbeous Sierra Finch | *Geospizopsis unicolor* |
| Plushcap | *Catamblyrhynchus diadema* |
| Prothonotary Warbler | *Protonotaria citrea* |
| Purple Gallinule | *Porphyrio martinica* |
| Purple Honeycreeper | *Cyanerpes caeruleus* |
| Purple-throated Woodstar | *Philodice mitchellii* |
| Purplish-mantled Tanager | *Iridosornis porphyrocephalus* |
| Red-and-green Macaw | *Ara chloropterus* |
| Red-bellied Grackle | *Hypopyrrhus pyrohypogaster* |
| Red-breasted Meadowlark | *Leistes militaris* |
| Red-capped Cardinal | *Paroaria gularis* |
| Red-crested Cotinga | *Ampelion rubrocristatus* |
| Red-crowned Woodpecker | *Melanerpes rubricapillus* |
| Red-eyed Vireo | *Vireo olivaceus* |
| Red-faced Spinetail | *Cranioleuca erythrops* |
| Red-headed Barbet | *Eubucco bourcierii* |
| Red-legged Honeycreeper | *Cyanerpes cyaneus* |
| Red-lored Amazon | *Amazona autumnalis* |
| Red-ruffed Fruitcrow | *Pyroderus scutatus* |
| Red-rumped Woodpecker | *Veniliornis kirkii* |
| Reddish Egret | *Egretta rufescens* |
| Ringed Kingfisher | *Megaceryle torquata* |
| Roadside Hawk | *Rupornis magnirostris* |
| Rock Pigeon | *Columba livia* |
| Rose-breasted Grosbeak | *Pheucticus ludovicianus* |
| Roseate Spoonbill | *Platalea ajaja* |
| Royal Tern | *Thalasseus maximus* |
| Ruddy Ground Dove | *Columbina talpacoti* |
| Ruddy-breasted Seedeater | *Sporophila minuta* |
| Rufescent Tiger-Heron | *Tigrisoma lineatum* |
| Rufous Motmot | *Baryphthengus martii* |
| Rufous-breasted Hermit | *Glaucis hirsutus* |
| Rufous-browed Conebill | *Conirostrum rufum* |
| Rufous-browed Peppershrike | *Cyclarhis gujanensis* |
| Rufous-collared Sparrow | *Zonotrichia capensis* |
| Rufous-crowned Tody-Flycatcher | *Poecilotriccus ruficeps* |
| Rufous-gaped Hillstar | *Urochroa bougueri* |
| Rufous-tailed Hummingbird | *Amazilia tzacatl* |
| Rufous-tailed Jacamar | *Galbula ruficauda* |
| Rufous-throated Tanager | *Ixothraupis rufigula* |
| Rufous-vented Chachalaca | *Ortalis ruficauda* |
| Russet-backed Oropendola | *Psarocolius angustifrons* |
| Russet-crowned Warbler | *Myiothlypis coronata* |
| Russet-throated Puffbird | *Hypnelus ruficollis* |
| Rusty Flowerpiercer | *Diglossa sittoides* |
| Rusty-margined Flycatcher | *Myiozetetes cayanensis* |
| Saffron Finch | *Sicalis flaveola* |
| Saffron-crowned Tanager | *Tangara xanthocephala* |
| Santa Marta Brushfinch | *Atlapetes melanocephalus* |
| Savanna Hawk | *Buteogallus meridionalis* |
| Scaled Dove | *Columbina squammata* |
| Scarlet Ibis | *Eudocimus ruber* |
| Scarlet Macaw | *Ara macao* |
| Scarlet Tanager | *Piranga olivacea* |
| Scarlet-bellied Mountain-Tanager | *Anisognathus igniventris* |
| Scarlet-fronted Parakeet | *Psittacara wagleri* |
| Scrub Greenlet | *Hylophilus flavipes* |
| Scrub Tanager | *Stilpnia vitriolina* |
| Semipalmated Plover | *Charadrius semipalmatus* |
| Shining Sunbeam | *Aglaeactis cupripennis* |
| Shiny Cowbird | *Molothrus bonariensis* |
| Short-tailed Hawk | *Buteo brachyurus* |
| Sickle-winged Guan | *Chamaepetes goudotii* |
| Silver-beaked Tanager | *Ramphocelus carbo* |
| Silver-throated Tanager | *Tangara icterocephala* |
| Slate-throated Redstart | *Myioborus miniatus* |
| Slaty-capped Flycatcher | *Leptopogon superciliaris* |
| Smoke-colored Pewee | *Contopus fumigatus* |
| Smoky-brown Woodpecker | *Leuconotopicus fumigatus* |
| Smooth-billed Ani | *Crotophaga ani* |
| Snail Kite | *Rostrhamus sociabilis* |
| Snowy Egret | *Egretta thula* |
| Social Flycatcher | *Myiozetetes similis* |
| Solitary Sandpiper | *Tringa solitaria* |
| Southern Beardless-Tyrannulet | *Camptostoma obsoletum* |
| Southern Emerald-Toucanet | *Aulacorhynchus albivitta* |
| Southern House Wren | *Troglodytes musculus* |
| Southern Lapwing | *Vanellus chilensis* |
| Southern Rough-winged Swallow | *Stelgidopteryx ruficollis* |
| Sparkling Violetear | *Colibri coruscans* |
| Speckled Chachalaca | *Ortalis guttata* |
| Speckled Hummingbird | *Adelomyia melanogenys* |
| Speckled Tanager | *Ixothraupis guttata* |
| Spectacled Owl | *Pulsatrix perspicillata* |
| Spectacled Parrotlet | *Forpus conspicillatus* |
| Spectacled Thrush | *Turdus nudigenis* |
| Spot-breasted Woodpecker | *Colaptes punctigula* |
| Spot-flanked Gallinule | *Porphyriops melanops* |
| Spotted Sandpiper | *Actitis macularius* |
| Steely-vented Hummingbird | *Saucerottia saucerottei* |
| Straight-billed Woodcreeper | *Dendroplex picus* |
| Streak-headed Woodcreeper | *Lepidocolaptes souleyetii* |
| Streak-throated Bush-Tyrant | *Myiotheretes striaticollis* |
| Streaked Flycatcher | *Myiodynastes maculatus* |
| Streaked Saltator | *Saltator striatipectus* |
| Streaked Xenops | *Xenops rutilans* |
| Striated Heron | *Butorides striata* |
| Striolated Manakin | *Machaeropterus striolatus* |
| Stripe-backed Wren | *Campylorhynchus nuchalis* |
| Striped Cuckoo | *Tapera naevia* |
| Striped Owl | *Asio clamator* |
| Stygian Owl | *Asio stygius* |
| Sulphur-bellied Flycatcher | *Myiodynastes luteiventris* |
| Summer Tanager | *Piranga rubra* |
| Sunbittern | *Eurypyga helias* |
| Superciliaried Hemispingus | *Thlypopsis superciliaris* |
| Swainson's Thrush | *Catharus ustulatus* |
| Swallow Tanager | *Tersina viridis* |
| Swallow-tailed Kite | *Elanoides forficatus* |
| Swallow-winged Puffbird | *Chelidoptera tenebrosa* |
| Sword-billed Hummingbird | *Ensifera ensifera* |
| Tennessee Warbler | *Leiothlypis peregrina* |
| Thick-billed Euphonia | *Euphonia laniirostris* |
| Thick-billed Seed-Finch | *Sporophila funerea* |
| Three-striped Warbler | *Basileuterus tristriatus* |
| Torrent Duck | *Merganetta armata* |
| Torrent Tyrannulet | *Serpophaga cinerea* |
| Toucan Barbet | *Semnornis ramphastinus* |
| Tourmaline Sunangel | *Heliangelus exortis* |
| Tricolored Heron | *Egretta tricolor* |
| Tropical Gnatcatcher | *Polioptila plumbea* |
| Tropical Kingbird | *Tyrannus melancholicus* |
| Tropical Mockingbird | *Mimus gilvus* |
| Tropical Parula | *Setophaga pitiayumi* |
| Tropical Screech-Owl | *Megascops choliba* |
| Turkey Vulture | *Cathartes aura* |
| Turquoise Dacnis | *Dacnis hartlaubi* |
| Tyrian Metaltail | *Metallura tyrianthina* |
| Velvet-purple Coronet | *Boissonneaua jardini* |
| Venezuelan Troupial | *Icterus icterus* |
| Vermilion Cardinal | *Cardinalis phoeniceus* |
| Vermilion Flycatcher | *Pyrocephalus rubinus* |
| Violaceous Jay | *Cyanocorax violaceus* |
| Violet-tailed Sylph | *Aglaiocercus coelestis* |
| Wattled Jacana | *Jacana jacana* |
| Western Cattle-Egret | *Ardea ibis* |
| Western Emerald | *Chlorostilbon melanorhynchus* |
| Whistling Heron | *Syrigma sibilatrix* |
| White Ibis | *Eudocimus albus* |
| White-bearded Manakin | *Manacus manacus* |
| White-bellied Woodstar | *Chaetocercus mulsant* |
| White-booted Racket-tail | *Ocreatus underwoodii* |
| White-capped Dipper | *Cinclus leucocephalus* |
| White-collared Swift | *Streptoprocne zonaris* |
| White-faced Whistling-Duck | *Dendrocygna viduata* |
| White-headed Marsh Tyrant | *Arundinicola leucocephala* |
| White-lined Tanager | *Tachyphonus rufus* |
| White-mantled Barbet | *Capito hypoleucus* |
| White-naped Brushfinch | *Atlapetes albinucha* |
| White-necked Jacobin | *Florisuga mellivora* |
| White-shouldered Tanager | *Loriotus luctuosus* |
| White-sided Flowerpiercer | *Diglossa albilatera* |
| White-tailed Hawk | *Geranoaetus albicaudatus* |
| White-tailed Kite | *Elanus leucurus* |
| White-tailed Starfrontlet | *Coeligena phalerata* |
| White-tailed Trogon | *Trogon chionurus* |
| White-throated Toucan | *Ramphastos tucanus* |
| White-throated Tyrannulet | *Mecocerculus leucophrys* |
| White-tipped Dove | *Leptotila verreauxi* |
| White-tipped Quetzal | *Pharomachrus fulgidus* |
| White-vented Plumeleteer | *Chalybura buffonii* |
| White-winged Becard | *Pachyramphus polychopterus* |
| White-winged Swallow | *Tachycineta albiventer* |
| Whooping Motmot | *Momotus subrufescens* |
| Willet | *Tringa semipalmata* |
| Wood Stork | *Mycteria americana* |
| Yellow Oriole | *Icterus nigrogularis* |
| Yellow-backed Oriole | *Icterus chrysater* |
| Yellow-bellied Chat-Tyrant | *Silvicultrix diadema* |
| Yellow-bellied Elaenia | *Elaenia flavogaster* |
| Yellow-bellied Seedeater | *Sporophila nigricollis* |
| Yellow-bellied Siskin | *Spinus xanthogastrus* |
| Yellow-billed Cuckoo | *Coccyzus americanus* |
| Yellow-breasted Brushfinch | *Atlapetes latinuchus* |
| Yellow-browed Sparrow | *Ammodramus aurifrons* |
| Yellow-chinned Spinetail | *Certhiaxis cinnamomeus* |
| Yellow-crowned Amazon | *Amazona ochrocephala* |
| Yellow-crowned Night Heron | *Nyctanassa violacea* |
| Yellow-eared Parrot | *Ognorhynchus icterotis* |
| Yellow-faced Grassquit | *Tiaris olivaceus* |
| Yellow-green Vireo | *Vireo flavoviridis* |
| Yellow-headed Caracara | *Daptrius chimachima* |
| Yellow-hooded Blackbird | *Chrysomus icterocephalus* |
| Yellow-legged Thrush | *Turdus flavipes* |
| Yellow-olive Flatbill | *Tolmomyias sulphurescens* |
| Yellow-rumped Cacique | *Cacicus cela* |
| Yellow-throated Toucan | *Ramphastos ambiguus* |
| Yellow-tufted Dacnis | *Dacnis egregia* |
| Yellow-tufted Woodpecker | *Melanerpes cruentatus* |

</details>

## Notas

- No hay tests ni configuración de linter en este repo.
- El primer mensaje que llegue tardará algunos segundos extra porque el modelo fastai se carga una
  sola vez al iniciar el proceso (`BirdClassificationService.__init__`).
