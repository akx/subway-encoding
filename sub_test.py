from sub_spec import subspec_from_grammar_file

SubSpec = subspec_from_grammar_file("grammar.txt")

sub = SubSpec(
    subType="salad",
    breadType="Juusto-Oregano",
    flavor="Italian BMT",
    cheeseType="american",
    doubleMeat=True,
    doubleCheese=True,
    heat=True,
    extraCheeseType="none",
    sauces={"Southwest": True, "Kevytmajoneesi": True, "Makea sipulikastike": True},
    vegetables={"jalapeno": True, "guacamole": True, "jäävuorisalaatti": True},
    extras={"Pippuri": True},
)

sub2 = SubSpec.from_bits(sub.to_bits())
sub3 = SubSpec.from_code(sub.to_code())

assert sub.to_code() == sub2.to_code(), (sub, sub2)
assert sub.to_code() == sub3.to_code(), (sub, sub3)
