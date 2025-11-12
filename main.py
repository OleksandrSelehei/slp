from etl.airflow_dags.dag_source_stace import run_process_stake_data


def main():
    run_process_stake_data()


if __name__ == '__main__':
    main()
