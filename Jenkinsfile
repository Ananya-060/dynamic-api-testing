pipeline {
    agent any

    environment {
        IMAGE_NAME = 'dynamic-testing-framework'
        IMAGE_TAG = 'latest'
        TEST_DATA_PATH = '/app/test_data3.xlsx'
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Build Docker Image') {
            steps {
                bat "docker build -t ${IMAGE_NAME}:${IMAGE_TAG} ."
            }
        }

        stage('Run Tests') {
            steps {
                withCredentials([file(credentialsId: 'test_data', variable: 'SECRET_FILE_PATH')]) {
                    bat """
                    if not exist reports mkdir reports
                    if not exist logs mkdir logs
                    docker run --rm -e TEST_DATA_PATH=${TEST_DATA_PATH} -v "${SECRET_FILE_PATH}:${TEST_DATA_PATH}" -v "%WORKSPACE%/reports:/app/reports" -v "%WORKSPACE%/logs:/app/logs" ${IMAGE_NAME}:${IMAGE_TAG} pytest -q tests/test_api_client.py tests/test_api_from_excel.py -s
                    """
                }
            }
        }
    }

    post {
        always {
            archiveArtifacts artifacts: 'reports/**, logs/**', allowEmptyArchive: true
        }
        success {
            echo 'Tests passed successfully.'
        }
        failure {
            echo 'Tests failed.'
        }
    }
}
