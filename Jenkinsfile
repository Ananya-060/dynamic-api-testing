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
                sh "docker build -t ${IMAGE_NAME}:${IMAGE_TAG} ."
            }
        }

        stage('Run Tests') {
            steps {
                sh '''
                mkdir -p reports logs
                docker run --rm \
                    -e TEST_DATA_PATH=${TEST_DATA_PATH} \
                    -v "$PWD/reports:/app/reports" \
                    -v "$PWD/logs:/app/logs" \
                    ${IMAGE_NAME}:${IMAGE_TAG} \
                    pytest -q tests/test_api_client.py tests/test_api_from_excel.py -s
                '''
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
