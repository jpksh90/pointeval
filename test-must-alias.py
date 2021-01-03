from must_alias import MustAlias

ma = MustAlias(benchmark='avrora', analysis='1cs', ir='soot')
aliases = ma.compute_must_alias()
print("#alias sets = ", len(list(aliases)))

for a in aliases:
    print(a)

ma = MustAlias(benchmark='avrora', analysis='1cs', ir='wala')
aliases = ma.compute_must_alias()
print("#alias sets = ", len(list(aliases)))
