from dataclasses import dataclass
from typing import Dict, List, Union
import requests
import logging

from .defi_safety_protocol import protocol

logger = logging.getLogger(__name__)

API_ENDPOINT = (
    'https://www.defisafety.com/api/pqrs?status=Active&reviewStatus=Completed'
)

etherscan_label_to_protocol_map = {
    '1inch.exchange': protocol['1inch.exchange'],
    'aave': protocol['aave v3'],
    'aave v2': protocol['aave v2'],
    'balancer': protocol['balancer v2'],
    'compound': protocol['compound'],
    'curve.fi': protocol['curve finance'],
    'fei protocol': None,
    'idle.finance': protocol['idle v4'],
    'inverse finance': protocol['inverse finance'],
    'lido': protocol['lido'],
    'liquity': protocol['liquity'],
    'maker': protocol['makerdao'],
    'old contract': None,
    'origin protocol': protocol['origin'],
    'pooltogether': protocol['pooltogether v4'],
    'reflexer finance': protocol['reflexer finance'],
    'reserve protocol': None,
    'shapeshift': protocol['shapeshift'],
    'sushiswap': protocol['sushiswap  v2'],
    'synthetix': protocol['synthetix pq'],
    'trusttoken': None,
    'usdc': None,
    'uniswap': protocol['uniswap v3'],
    'vaults': None,
    'vesper finance': protocol['vesper'],
    'wrapped bitcoin': None,
    'yearn.finance': protocol['yearn finance v2'],
    'ygov.finance': None
}


@dataclass
class DeFiSafetyScores:
    overallScore: float
    contractsAndTeamScore: Union[float, None] = None
    documentationScore: Union[float, None] = None
    testingScore: Union[float, None] = None
    securityScore: Union[float, None] = None
    adminControlsScore: Union[float, None] = None
    oraclesScore: Union[float, None] = None

    def __add__(self, other):
        new_score = DeFiSafetyScores(self.overallScore + other.overallScore)
        for key in new_score.__dict__.keys():
            if key == 'overallScore':
                continue
            self_score = getattr(self, key)
            other_score = getattr(other, key)
            if self_score is not None and other_score is not None:
                setattr(new_score, key, self_score + other_score)
        return new_score

    def __radd__(self, other):
        if other == 0:
            return self
        else:
            return self.__add__(other)

    def __truediv__(self, scalar):
        new_score = DeFiSafetyScores(self.overallScore / scalar)
        for key in new_score.__dict__.keys():
            if key == 'overallScore':
                continue
            self_score = getattr(self, key)
            if self_score is not None:
                setattr(new_score, key, self_score / scalar)
        return new_score


class DeFiSafety:
    _scores: Dict[str, DeFiSafetyScores]

    """
    Protocol risk scores from DeFi Safety
    """

    def __init__(self):
        self._scores = None

    def load_scores(self):
        pqrs = []
        offset = 0
        no_data = False
        while not no_data:
            url = API_ENDPOINT + '&offset=' + str(offset)
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()['data']
                no_data = len(data) == 0
                pqrs.extend(data)
                offset += 20
            else:
                break
        self._scores = {}
        for pqr in pqrs:
            scores = DeFiSafetyScores(pqr['overallScore'])
            for score in pqr['breakdowns']:
                name = score['name'].lower()
                score = score['percentage']
                if score is not None:
                    score = float(score)

                if 'team' in name:
                    scores.contractsAndTeamScore = score
                elif 'documentation' in name:
                    scores.documentationScore = score
                elif 'test' in name:
                    scores.testingScore = score
                elif 'security' in name:
                    scores.securityScore = score
                elif 'control' in name:
                    scores.adminControlsScore = score
                elif 'oracle' in name:
                    scores.oraclesScore = score
            self._scores[pqr['title']] = scores

    @property
    def protocols(self) -> List[str]:
        if self._scores is None:
            self.load_scores()
        return list(self._scores.keys())

    def scores(self, name: str) -> Dict[str, DeFiSafetyScores]:
        if self._scores is None:
            self.load_scores()
        candidates = {}
        for k, v in self._scores.items():
            name_lower = name.lower()
            mapper = etherscan_label_to_protocol_map
            is_matching_protocol = mapper.get(name_lower) == k

            if is_matching_protocol or name_lower in k.lower():
                candidates[k] = v
                break
        return candidates
