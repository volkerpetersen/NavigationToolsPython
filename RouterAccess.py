import os
#import subprocess
x = [1]
for y in range(0, 10):
    for z in range(0, 10):
        for l in range(0, 10):
            for m in range(0, 10):
                for n in range(0, 10):
                    for o in range(0, 10):
                        for p in range(0, 10):
                            for q in range(0, 10):
                                password = [y, z, l, m, n, o, p, q]
                                str1 = ''.join(str(e)for e in password)
                                print("trying pass: '%s'" % str1)
                                #proc = subprocess.Popen(["networksetup", "-setairportnetwork","en0","Vodafone_ADSL_903F",str1],stdout=subprocess.PIPE)
                                # x=proc.stdout.readline()
                                x[0] = "N"
                                try:
                                    # output generated if password os wrong is"False network password" so I take the first letter F and check it
                                    if (x[0] == 'F'):
                                        print("trying next password")
                                # if password is correct there's no command reply hence no string to access it with x[0]
                                except IndexError:
                                    print("Password found !")
                                    break
