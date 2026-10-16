"""Explicit prospective permission, separate from the fixed retrospective seal."""
from dataclasses import dataclass


@dataclass(frozen=True)
class ProspectiveScope:
    cutoff: int

    def __post_init__(self):
        if type(self.cutoff) is not int or not 104<=self.cutoff<=1245:
            raise ValueError('Prospective source cutoff must be104..1245 during Phase5')

    @property
    def target(self): return self.cutoff+1

    def history(self,rows):
        if rows.empty or rows.draw_no.tolist()!=list(range(1,self.cutoff+1)):
            raise ValueError('Prospective history must be exactly1..cutoff; future observations forbidden')

    def training(self,rows,cutoff):
        if cutoff!=self.cutoff or rows.empty or rows.target_draw.max()>self.cutoff:
            raise ValueError('Prospective fitting cannot access target or later labels')

    def current(self,rows):
        if rows.empty or not rows.target_draw.eq(self.target).all():
            raise ValueError('Prospective scoring is restricted to cutoff+1')
