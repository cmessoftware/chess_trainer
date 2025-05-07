import seaborn as sns
import matplotlib.pyplot as plt

def plot_blunders(df, output_path):
    """
    Generate a bar plot of blunder distribution and save it to output_path.
    
    Args:
        df (pandas.DataFrame): DataFrame containing a column 'is_blunder' (boolean).
        output_path (str): Path to save the plot.
    """
    sns.countplot(data=df, x="is_blunder")
    plt.title("Distribución de Errores Graves")
    plt.xlabel("Es Blunder")
    plt.ylabel("Cantidad")
    plt.savefig(output_path)
    plt.close()