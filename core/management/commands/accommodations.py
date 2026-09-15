from django.core.management.base import BaseCommand
from core.models import University, Accommodation

# a dictionary of universities, where each university corresponds to a list of tuples
# each tuple in the list contains the information to an accommodation at that university
# the tuple structure is as follows: 
# ("accommodation name",offers catered, offeres self catered, offeres en suite, offers shared bathroom
# rent catered en suite, rent catered shared, rent self catered en suite, rent self catered shared)
# the data in this dictionary was searched and aggregated by claude, although i validated it myself and it is accurate

UNIVERSITIES = {
    "University of Leeds": [
        ("Blenheim Point", False, True, True, False, None, None, 203.50, None),
        ("Carlton Hill", False, True, True, False, None, None, 215.50, None),
        ("Central Village", False, True, True, False, None, None, 206.50, None),
        ("Charles Morris Hall", True, True, True, True, 259.00, 244.00, 220.00, None),
        ("CitySide", False, True, True, False, None, None, 215.50, None),
        ("Devonshire Hall", True, True, True, True, 255.00, 225.00, 189.00, 161.50),
        ("Ellerslie Global Residence", True, False, True, True, 268.50, 235.50, None, None),
        ("Henry Price Residences", False, True, True, True, None, None, 201.50, 177.00),
        ("Hepworth Lodge", False, True, True, False, None, None, 169.00, None),
        ("James Baillie Park", False, True, True, True, None, None, 199.00, 167.50),
        ("Leodis Residences", False, True, True, False, None, None, 191.00, None),
        ("Lupton Residences", False, True, False, True, None, None, None, 125.00),
        ("Lyddon Hall", True, False, True, True, 274.00, 236.50, None, None),
        ("Montague Burton", False, True, False, True, None, None, None, 164.00),
        ("North Hill Court", False, True, False, True, None, None, None, 144.50),
        ("Oak House", False, True, True, False, None, None, 182.50, None),
        ("Royal Park Flats", False, True, False, True, None, None, None, 132.00),
        ("Sentinel Towers", False, True, True, False, None, None, 163.00, None),
        ("Shared Houses", False, True, False, True, None, None, None, 143.50),
        ("St Marks Residence", False, True, True, False, None, None, 195.50, None),
        ("The Plaza", False, True, True, False, None, None, 170.00, None),
        ("White Rose View", False, True, True, False, None, None, 203.00, None),
    ],
    "University of Manchester": [
        ("Ashburne Hall", True, False, False, True, None, 189.12, None, None),
        ("Burkhardt House", False, True, True, False, None, None, 179.83, None),
        ("Canterbury Court", False, True, True, False, None, None, 179.83, None),
        ("Daisy Bank", False, True, True, False, None, None, 224.55, None),
        ("Dalton-Ellis Hall", True, False, True, True, 245.73, 194.07, None, None),
        ("Denmark Road", False, True, True, False, None, None, 234.00, None),
        ("George Kenyon", False, True, True, False, None, None, None, None),
        ("Horniman House", False, True, True, False, None, None, None, None),
        ("Hulme Hall", True, False, False, True, None, 200.85, None, None),
        ("Kincardine Court", False, True, True, False, None, None, 258.00, None),
        ("Manchester Gardens", False, True, True, True, None, None, 230.00, 175.00),
        ("Park View", False, True, True, False, None, None, None, None),
        ("Piccadilly Point", False, True, True, False, None, None, None, None),
        ("Richmond Park", False, True, True, False, None, None, 179.83, None),
        ("Rusholme Place", False, True, True, False, None, None, 198.64, None),
        ("Sheavyn House", False, True, True, False, None, None, 179.83, None),
        ("Square Gardens", False, True, True, False, None, None, 225.74, None),
        ("St Anselm Hall", True, False, True, True, 241.00, 196.00, None, None),
        ("Unsworth Park", False, True, True, False, None, None, 226.60, None),
        ("Uttley House", False, True, True, False, None, None, 207.24, None),
        ("Victoria Point", False, True, True, False, None, None, None, None),
        ("Weston Hall", False, True, True, False, None, None, 197.62, None),
        ("Whitworth Park", False, True, False, True, None, None, None, 121.93),
        ("Wilmslow Park", False, True, True, False, None, None, 230.00, None),
        ("Woolton Hall", True, False, False, True, None, None, None, None),
    ],
    "Newcastle University": [
        ("Castle Leazes", True, True, False, True, None, None, None, None),
        ("Henderson Hall", True, True, False, True, None, None, None, None),
        ("Park View", False, True, True, False, None, None, 197.40, None),
        ("Marris House", False, True, True, False, None, None, None, None),
        ("Leazes Parade", False, True, False, True, None, None, None, None),
        ("The View", False, True, True, False, None, None, None, None),
        ("Verde", False, True, True, False, None, None, None, None),
        ("Newgate Court", False, True, True, False, None, None, None, None),
        ("Wellington St Plaza", False, True, True, False, None, None, None, None),
        ("Kensington Terrace", False, True, True, False, None, None, 197.40, None),
        ("Park Terrace", False, True, True, False, None, None, 197.40, None),
        ("Windsor Terrace", False, True, True, True, None, None, None, None),
        ("Bernicia", False, True, True, False, None, None, None, None),
        ("Manor Bank", False, True, True, False, None, None, None, None),
        ("Carlton Lodge", False, True, True, False, None, None, None, None),
        ("Jesmond Road", False, True, True, False, None, None, None, None),
        ("Grand Hotel", False, True, True, False, None, None, None, None),
        ("Bowsden Court", False, True, True, False, None, None, None, None),
        ("Byron Central", False, True, True, False, None, None, None, None),
        ("Turner Court", False, True, True, False, None, None, None, None),
        ("Rosedale Court", False, True, True, False, None, None, None, None),
        ("Easton Flats", False, True, True, False, None, None, None, None),
    ],
    "University of York": [
        ("Alcuin College", False, True, True, False, None, None, 206.00, None),
        ("Anne Lister College", False, True, True, False, None, None, 222.00, None),
        ("Constantine College", False, True, True, True, None, None, 219.50, 208.00),
        ("David Kato College", False, True, True, False, None, None, 222.00, None),
        ("Derwent College", True, False, True, True, None, 227.50, None, None),
        ("Goodricke College", False, True, True, True, None, None, 222.00, 193.00),
        ("Halifax College", False, True, True, True, None, None, 215.00, 167.50),
        ("James College", True, False, True, True, None, 244.00, None, None),
        ("Langwith College", False, True, True, True, None, None, 219.50, 208.00),
        ("Vanbrugh College", True, False, True, True, None, 267.50, None, None),
        ("Wentworth College", False, True, True, False, None, None, 215.00, None),
    ],
    "University of Nottingham": [
        ("Ancaster Hall", False, True, True, False, None, None, None, None),
        ("Beeston Hall", False, True, False, True, None, None, None, None),
        ("Cavendish Hall", False, True, False, True, None, None, None, None),
        ("Cripps Hall", False, True, False, True, None, None, None, None),
        ("Derby Hall", False, True, False, True, None, None, None, None),
        ("Florence Boot Hall", False, True, False, True, None, None, None, None),
        ("Hugh Stewart Hall", False, True, False, True, None, None, None, None),
        ("Lenton & Lincoln Hall", False, True, True, False, None, None, None, None),
        ("Melton Hall", False, True, False, True, None, None, None, None),
        ("Newark Hall", False, True, False, True, None, None, None, None),
        ("Nightingale Hall", False, True, False, True, None, None, None, None),
        ("Rutland Hall", False, True, False, True, None, None, None, None),
        ("Sherwood Hall", False, True, False, True, None, None, None, None),
        ("Southwell Hall", False, True, False, True, None, None, None, None),
        ("Willoughby Hall", False, True, False, True, None, None, None, None),
        ("Wortley Hall", False, True, False, True, None, None, None, None),
    ],
    "University of Sheffield": [
        ("Allen Court", False, True, True, False, None, None, 194.32, None),
        ("St Vincent's Place", False, True, True, False, None, None, 180.02, None),
        ("St George's Flats", False, True, True, False, None, None, 180.02, None),
        ("Burbage", False, True, True, False, None, None, 195.72, None),
        ("Cratcliffe", False, True, True, False, None, None, 195.72, None),
        ("Crescent Flats", False, True, False, True, None, None, None, 151.41),
        ("Crewe Flats", False, True, False, True, None, None, None, 157.12),
        ("Endcliffe Vale Flats", False, True, False, True, None, None, None, 151.41),
        ("Howden", False, True, True, False, None, None, 195.72, None),
        ("Kinder", False, True, True, False, None, None, 227.68, None),
        ("Laddow", False, True, True, False, None, None, 240.38, None),
        ("Lawrencefield", False, True, True, False, None, None, 195.72, None),
        ("Ramshaw", False, True, True, False, None, None, 195.72, None),
        ("Ravenstone", False, True, True, False, None, None, 195.72, None),
        ("Rivelin", False, True, True, False, None, None, 195.72, None),
        ("Stephenson", True, False, False, True, None, 194.46, None, None),
        ("Windgather", False, True, True, False, None, None, 227.68, None),
    ],
    "University of Bath": [
        ("Aquila Court", False, True, True, False, None, None, None, None),
        ("Brendon Court", False, True, True, False, None, None, None, None),
        ("Canal Wharf", False, True, True, False, None, None, None, None),
        ("Carpenter House", False, True, True, False, None, None, None, None),
        ("Centurion House", False, True, True, False, None, None, None, None),
        ("Clevelands Building", False, True, False, True, None, None, None, None),
        ("Cotswold House", False, True, False, True, None, None, None, None),
        ("Eastwood Green", False, True, True, False, None, None, None, None),
        ("Eveleigh Waterside", False, True, True, False, None, None, None, None),
        ("The Brook", False, True, True, False, None, None, None, None),
        ("The Quads", False, True, True, False, None, None, None, None),
        ("Thornbank Gardens", False, True, False, True, None, None, None, None),
        ("Westwood", False, True, False, True, None, None, None, None),
    ],
    "Northumbria University": [
        ("Camden Court", False, True, True, False, None, None, None, None),
        ("Claude Gibb", False, True, False, True, None, None, None, None),
        ("Glenamara House", False, True, True, False, None, None, None, None),
        ("Lovaine Hall", False, True, False, True, None, None, None, None),
        ("New Bridge Street", False, True, True, False, None, None, None, None),
        ("Trinity Square", False, True, True, False, None, None, None, None),
        ("Winn", False, True, True, False, None, None, None, None),
    ],
}

# class to transfer the data within the dictionary into an SQLite databse via djangos ORM
# doesnt overwrite cells (other than boolean values) so can safely be run over and over again

class Command(BaseCommand):
    help = "Fills in all of the university information into SQLite"

    def handle(self, *args, **options):
        # loops over every university and its list of accommodations
        for uni_name, halls in UNIVERSITIES.items():
            university, created = University.objects.get_or_create(name=uni_name)
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created {uni_name}"))

            added = 0
            updated = 0
            # now looping over every accommodation within each university
            for (name, catered, self_catered, en_suite, shared,
                 rent_c_ens, rent_c_shr, rent_s_ens, rent_s_shr) in halls:
                # creates the hall in the SQLite database if it doesn't exist yet, otherwise it is fetched
                obj, was_created = Accommodation.objects.get_or_create(
                    university=university,
                    name=name,
                    defaults={
                        "offers_catered": catered,
                        "offers_self_catered": self_catered,
                        "offers_en_suite": en_suite,
                        "offers_shared_bathroom": shared,
                        "rent_catered_ensuite": rent_c_ens,
                        "rent_catered_shared": rent_c_shr,
                        "rent_self_catered_ensuite": rent_s_ens,
                        "rent_self_catered_shared": rent_s_shr,
                    },
                )
                if was_created:
                    added += 1
                # if the hall already exists only data that has changed in the dictionsry is updated in the database
                else:
                    fields = {
                        "offers_catered": catered,
                        "offers_self_catered": self_catered,
                        "offers_en_suite": en_suite,
                        "offers_shared_bathroom": shared,
                    }
                    rent_fields = {
                        "rent_catered_ensuite": rent_c_ens,
                        "rent_catered_shared": rent_c_shr,
                        "rent_self_catered_ensuite": rent_s_ens,
                        "rent_self_catered_shared": rent_s_shr,
                    }
                    changed = []
                    # booleans take the values from the dictionaries tuples
                    for f, v in fields.items():
                        if getattr(obj, f) != v:
                            setattr(obj, f, v)
                            changed.append(f)
                    # rent only overwrites if it has a value
                    for f, v in rent_fields.items():
                        if v is not None and getattr(obj, f) != v:
                            setattr(obj, f, v)
                            changed.append(f)
                    if changed:
                        obj.save(update_fields=changed)
                        updated += 1

            self.stdout.write(self.style.SUCCESS(f"{uni_name}: added {added}, updated {updated}."))