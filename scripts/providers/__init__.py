"""Provider contracts: local free content is the only enabled default."""
from abc import ABC,abstractmethod
import copy,json,unicodedata
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]

class ScriptProvider(ABC):
    @abstractmethod
    def create(self,topic):pass

class ImageProvider(ABC):
    @abstractmethod
    def resolve(self,asset_id):pass

class LocalScriptProvider(ScriptProvider):
    id='curated-local-v1'
    def create(self,topic):
        normalized=''.join(c for c in unicodedata.normalize('NFD',topic.lower()) if unicodedata.category(c)!='Mn')
        catalog=json.loads((ROOT/'content/catalog.json').read_text())
        choices=[entry for entry in catalog['topics'] if entry.get('published',True) and (normalized==entry['id'] or any(term in normalized for term in entry['keywords']))]
        if len(choices)>1:raise ValueError('Tema ambiguo: selecciona una sola entrada del catálogo publicado.')
        for entry in choices:
            if entry.get('published',True):
                story=json.loads((ROOT/entry['story']).read_text());story['provider']={'id':self.id,'topic_id':entry['id'],'requested_topic':topic,'generative_ai':False}
                return story
        raise ValueError('Tema aún no disponible. Selecciona un tema del catálogo publicado; no se sustituirá por otro vídeo.')

class LocalImageProvider(ImageProvider):
    id='original-blender-library-v1'
    def resolve(self,asset_id):
        from scripts.cinematic import verify_assets
        assets=verify_assets()
        if asset_id in assets:return copy.deepcopy(assets[asset_id])
        catalog=json.loads((ROOT/'content/catalog.json').read_text())
        for entry in catalog['topics']:
            if entry.get('published',True) and entry.get('asset_manifest') and asset_id.startswith(entry['id']+'_'):
                scoped=verify_assets(entry['asset_manifest'])
                if asset_id in scoped:return copy.deepcopy(scoped[asset_id])
        raise ValueError('Recurso visual no publicado en la biblioteca.')

class ChatGPTProvider(ScriptProvider):
    """Future seam only: deliberately no HTTP client, keys or paid requests."""
    id='chatgpt-disabled'
    def create(self,topic):raise RuntimeError('ChatGPT no está activado. No se permiten llamadas API de pago.')

def get_script_provider(name='curated-local-v1'):
    if name==LocalScriptProvider.id:return LocalScriptProvider()
    if name==ChatGPTProvider.id:return ChatGPTProvider()
    raise ValueError('Proveedor no autorizado.')
