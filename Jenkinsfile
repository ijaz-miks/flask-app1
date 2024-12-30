pipeline {
    agent any

    environment {
        APP_NAME = "flask-app1"
        DOCKER_IMAGE = "${env.APP_NAME}:${BUILD_NUMBER}"
        ECR_REPO = "public.ecr.aws/o0y6x7h1/sampleapp/flask-app1" // Your ECR repo
        AWS_REGION = "eu-central-1" // Your AWS region
    }

    stages {
        stage('Clone') {
            steps {
                git branch: 'master', url: 'git@github.com:ijaz-miks/flask-app1.git'
            }
        }

        stage('Build and Test') {
            steps {
                script {
                    // Build the Docker image
                    docker.build("$DOCKER_IMAGE")

                    // Run tests inside the container
                    def testExitCode = sh(script: "docker run $DOCKER_IMAGE python -m unittest test_app.py", returnStatus: true)
                    if (testExitCode != 0) {
                        error "Unit tests failed!"
                    }
                }
            }
        }

        stage('Push to ECR') {
            steps {
                script {
                    // Authenticate with ECR
                    docker.withRegistry("https://${ECR_REPO.substring(0, ECR_REPO.lastIndexOf('/'))}", "ecr:{$AWS_REGION}:jenkins-ecr") {

                        // Tag the image for ECR
                        docker.image("$DOCKER_IMAGE").tag("${ECR_REPO}:${BUILD_NUMBER}")

                        // Push the image to ECR
                        docker.image("${ECR_REPO}:${BUILD_NUMBER}").push()
                    }
                }
            }
        }

        // You can add a 'Deploy to EKS' stage later
    }

    // Optional: Add post-build actions like notifications
}