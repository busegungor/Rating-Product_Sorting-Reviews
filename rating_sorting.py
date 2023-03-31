import glob
import pandas as pd
import math
import scipy.stats as st


def read_file(filename):
    files = glob.glob(f"**/{filename}.*", recursive=True)
    if len(files) == 0:
        raise FileNotFoundError(f"The file '{filename}' could not be found.")
    file = files[0]
    if file.endswith(".csv"):
        pd.set_option("display.max_columns", None)
        pd.set_option("display.max_row", None)
        pd.set_option("display.width", 500)
        pd.set_option("display.expand_frame_repr", False)
        pd.set_option("display.float_format", lambda x: "%.5f" % x)
        return pd.read_csv(file, low_memory=False)
    elif file.endswith(".xlsx"):
        return pd.read_excel(file)
    elif file.endswith(".json"):
        with open(file, "r") as f:
            return pd.read_json(f)
    else:
        with open(file, "r") as f:
            return f.read()
# 1.The glob module is used to find all files with the given name and any extension, regardless of their location.
# The glob.glob function is called with the pattern **/{filename}.*,
# which means "search recursively from the current directory for any file with the given name and any extension".
# The result is a list of filenames that match the pattern.
# 2.If no files are found, a FileNotFoundError is raised with a message indicating that the file could not be found.
# If one or more files are found, the first file in the list is chosen to be read.
# This is done using the line file = files[0].
# 3.It does the required reading by selecting the appropriate extension.
df_ = read_file("kindle_reviews")
df = df_.copy()

# About Dataset
# Context
# A small subset of dataset of product reviews from Amazon Kindle Store category.

# Content
# 5-core dataset of product reviews from Amazon Kindle Store category from May 1996 - July 2014.
# Contains total of 982619 entries.
# Each reviewer has at least 5 reviews and each product has at least 5 reviews in this dataset.

# Columns
# asin - ID of the product, like B000FA64PK
# helpful - helpfulness rating of the review - example: 2/3.
# overall - rating of the product.
# reviewText - text of the review (heading).
# reviewTime - time of the review (raw).
# reviewerID - ID of the reviewer, like A3SPTOKDG7WBLN
# reviewerName - name of the reviewer.
# summary - summary of the review (description).
# unixReviewTime - unix timestamp.

def check_df(dataframe):
    print(" SHAPE ".center(70,'~'))
    print(dataframe.shape)
    print(" TYPES ".center(70,'~'))
    print(dataframe.dtypes)
    print(" HEAD ".center(70,'~'))
    print(dataframe.head())
    print(" MISSING VALUES ".center(70,'~'))
    print(dataframe.isnull().sum())
    print(" DESCRIBE ".center(70,'~'))
    print(dataframe.describe().T)
check_df(df)

df = df.dropna()
df.drop("Unnamed: 0", axis=1, inplace=True)

df = df.loc[df["asin"] == "B00BTIDW4S"]

df["overall"].value_counts()
# 5    484
# 4    201
# 3     60
# 2     23
# 1     13
# Name: overall, dtype: int64
df["overall"].mean() # 4.434058898847631

df["reviewTime"] = pd.to_datetime(df["reviewTime"])
df["reviewTime"].max() # Timestamp('2014-07-17 00:00:00')
current_date = pd.to_datetime("2014-7-19")
df["days"] = (current_date - df["reviewTime"]).dt.days

df.describe().T # 2.00000        279.00000        396.00000        449.00000        490.00000

df.loc[df["days"] <= 279, "overall"].mean() # 4.309644670050761
df.loc[(df["days"] > 279) & (df["days"] <= 396), "overall"].mean() # 4.441025641025641
df.loc[(df["days"] > 396) & (df["days"] <= 449), "overall"].mean() # 4.523076923076923
df.loc[df["days"] > 449, "overall"].mean() # 4.463917525773196

def time_based_weighted_average(dataframe, w1=28, w2=26, w3=24, w4=22):
    return df.loc[df["days"] <= 277, "overall"].mean() * w1 / 100 + \
           df.loc[(df["days"] > 277) & (df["days"] <= 394), "overall"].mean() * w2 / 100 + \
           df.loc[(df["days"] > 394) & (df["days"] <= 447), "overall"].mean() * w3 / 100 + \
           df.loc[df["days"] > 447, "overall"].mean() * w4 / 100

time_based_weighted_average(df) # 4.427965840632191
time_based_weighted_average(df, w1=30, w2=28, w3=22, w4=20) # 4.422926053021412
time_based_weighted_average(df, w1=32, w2=30, w3=20, w4=18) # 4.417886265410634


df[["helpful_yes", "helpful_yes_no"]] = df["helpful"].str.split(",", expand=True)
df["helpful_yes"] = df["helpful_yes"].str.strip("[").astype(int)
df["helpful_yes_no"] = df["helpful_yes_no"].str.strip("]").astype(int)

df["helpful_no"] = df["helpful_yes_no"] - df["helpful_yes"]


def up_down_difference_score_sorting(up, down):
    return up - down
def average_rating_score_sorting(up, down):
    if up + down == 0:
        return 0
    return up / (up + down)
def wilson_lower_bound(up, down, confidence=0.95):
    n = up + down
    if n == 0:
        return 0
    z = st.norm.ppf(1 - (1 - confidence) / 2)
    phat = 1.0 * up / n
    return (phat + z * z / (2 * n) - z * math.sqrt((phat * (1 - phat) + z * z / (4 * n)) / n)) / (1 + z * z / n)

df["up_down_difference"] = df.apply(lambda x: up_down_difference_score_sorting(x["helpful_yes"], x["helpful_no"]), axis=1)
df["average_rating"] = df.apply(lambda x: average_rating_score_sorting(x["helpful_yes"], x["helpful_no"]), axis=1)
df["WLB"] = df.apply(lambda x: wilson_lower_bound(x["helpful_yes"], x["helpful_no"]), axis=1)

df[["reviewText","helpful_yes", "helpful_no", "up_down_difference", "average_rating", "WLB"]].sort_values("WLB", ascending=False).head(20)

#                                                reviewText  helpful_yes  helpful_no  up_down_difference  average_rating     WLB
# 462504  I love werewolves. Totally and completely. So ...          110          12                  98         0.90164 0.83592
# 462467  I debated writing this review since I had alre...          133          43                  90         0.75568 0.68718
# 462614  I had read some really good reviews about this...           10           1                   9         0.90909 0.62264
# 462356  When I first downloaded this book I was skepti...           30           9                  21         0.76923 0.61664
# 462341  I have to admit that the genre of paranormal r...            6           0                   6         1.00000 0.60967
# 462210  I don't care about throbbing thighs sex scenes...           33          11                  22         0.75000 0.60559
# 462140  I decided to write this in hopes that it will ...           40          15                  25         0.72727 0.59768
# 462031  Maybe I had high hopes for this book because o...            8           2                   6         0.80000 0.49016
# 462061  I really enjoyed this book and you can't beat ...            3           0                   3         1.00000 0.43850
# 461934  This was the first shapeshifter romance I ever...            6           2                   4         0.75000 0.40928
# 461936  If you were fortunate enough to get this book ...            6           2                   4         0.75000 0.40928
# 462237  NTM author so decided to try THE MATING back i...            4           1                   3         0.80000 0.37553
# 462419  I can't say that I have never read a book this...            5           2                   3         0.71429 0.35893
# 462420  This book was a true pleasure. The characters ...            5           2                   3         0.71429 0.35893
# 461978  This book just pissed me off. Elise is such a ...            6           3                   3         0.66667 0.35420
# 462201  The Mating starts out with an interesting prem...            2           0                   2         1.00000 0.34238
# 462246  If you are into werewolves then you'll like th...            2           0                   2         1.00000 0.34238
# 462536  I loved this book, was my favorte out of the w...            3           1                   2         0.75000 0.30064
# 462109  Loved the first book in this series. The story...            3           1                   2         0.75000 0.30064
# 462492  I thought this was a good werewolf story. It w...            3           1                   2         0.75000 0.30064


