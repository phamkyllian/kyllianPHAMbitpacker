# Projet BitPacking

## Comment utiliser

### Installer
```python
git clone {repository}
```
### Utiliser

```python
# Importer la fonction factory de la librairie 
from BitPacker import bit_packer_factory
# générer un tableau d'entier
array = [1,2,4,5,205,1045,1023,2,4,4]
# choisir la méthode (crossing ou nocrossing)
packer = bit_packer_factory('crossing', array)
# compresser le tableau
packer.compress()
# Créer un packer avec un tableau vide
unpacker = bit_packer_factory('crossing', [])
# Décompresser le tableau compressé
ints: List[int] = unpacker.uncompress(packer.compressed)
# Retrouver un entier par sa position dans le tableau intiial
packer.get(3)

### Mesure de la performance
for key in packer.benchmark.keys():
    print('[bench packer] ', key, ' took ', packer.benchmark[key], 'seconds')

for key in unpacker.benchmark.keys():
    print('[bench unpacker] ', key, ' took ', unpacker.benchmark[key], 'seconds')
```

### TestCase
Il est possible d'utiliser le TestCase écrit dans le fichier main.py