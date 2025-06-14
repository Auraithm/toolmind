import os
import yaml
from tqdm import tqdm
from typing import Callable

def download_dataset(name: str = None, config: str = None, download_dir: str = "./", format: str = "parquet", use_hf_mirror: bool = False) -> None:
    """
    Download dataset and save to specified directory
    Args:
        name: Dataset name
        config: Dataset configuration
        download_dir: Download directory
        format: Dataset format
        use_hf_mirror: Whether to use hf-mirror mirror
    Returns:
        None
    """
    try:
        # 如果没配置代理，可以使用hf-mirror镜像
        if use_hf_mirror:
            os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"

        import datasets
        # 从yaml文件中读取数据集名称映射
        yaml_path = os.path.join(os.path.dirname(__file__), "dataset_name.yaml")
        with open(yaml_path, "r") as f:
            dataset_mapping = yaml.safe_load(f)["dataset_mapping"]
        try:
            dataset_name = dataset_mapping[name]
        except KeyError:
            print(f"Current Support Datasets: {dataset_mapping.keys()}. You can add your own dataset to the datasets/dataset_name.yaml file.")
            return
        print(f"Dataset: {name} is downloading from {dataset_name}...")
        # name = "GSM8K"
        if config is not None:
            configs = [config]
        else:
            # 首先尝试获取数据集的所有可用配置
            configs = datasets.get_dataset_config_names(dataset_name)
            print(f"This dataset has {len(configs)} configs: {configs}. We will download all of them.")

        # 如果有配置，使用第一个配置
        for config in configs:
            # 创建分支的文件夹
            if config != "default":
                branch_dir = os.path.join(download_dir, name, config)
            else:
                branch_dir = os.path.join(download_dir, name)
            print(f"SubDataset {config} is downloading to {branch_dir}...")
            os.makedirs(branch_dir, exist_ok=True)
            dataset = datasets.load_dataset(dataset_name, config)
            print(dataset)
            # 如果只有一个train 或者一个test划分，则复制一份到另外一边
            if len(dataset.keys()) == 1:
                if "train" in dataset:
                    dataset["test"] = dataset["train"]
                elif "test" in dataset:
                    dataset["train"] = dataset["test"]
                else:
                    raise ValueError(f"Dataset {config} has no train or test split.")
            # 保存每个划分
            for split in tqdm(dataset.keys(), desc=f"Downloading ..."):
                if format == "parquet":
                    dataset[split].to_parquet(os.path.join(branch_dir, f"{split}.parquet"))
                elif format == "json":
                    dataset[split].to_json(os.path.join(branch_dir, f"{split}.json"))
                elif format == "csv":
                    dataset[split].to_csv(os.path.join(branch_dir, f"{split}.csv"))
                elif format == "jsonl":
                    dataset[split].to_json(os.path.join(branch_dir, f"{split}.jsonl"))
                else:
                    raise ValueError(f"Unsupported format: {format}")

            print(f"Dataset {config} has been downloaded to {branch_dir}.")

    except Exception as e:
        print(f"Error: {str(e)}")
        if "ConnectionError:" in str(e):
            print("ConnectionError: Retrying with hf-mirror...")
            download_dataset(name, config, download_dir, format, use_hf_mirror=True)
        else:
            raise e

def load_dataset(path: str = None, config: str = "default", split = None) -> None:
    """
    Load a dataset from a path
    Args:
        path: Path to the dataset
        config: Configuration of the dataset
        split: Split of the dataset
    Returns:
        Dataset
    """
    import datasets
    if config not in ["default"]:
        dataset = datasets.load_dataset(os.path.join(path, config), split=split)
    else:
        dataset = datasets.load_dataset(path)[split]
    return dataset

def apply_func(dataset, func: Callable, remove_columns: bool = True):
    """
    Apply a function to a dataset
    Args:
        dataset: Dataset
        func: Function to apply
        remove_columns: Whether to remove old columns
    Returns:
        Dataset
    """
    dataset = dataset.map(func, with_indices=True, remove_columns=remove_columns)
    return dataset

if __name__ == "__main__":
    download_dataset(name="MATH-500", config="default", download_dir="data/")
