from app.wh.domain.customer.customer import Customer
from app.wh.domain.product.product_request import ProductRequest
from app.wh.domain.request.customer_request import CustomerRequest


class MailToCustomerRequestMapper:

    def map(

        self,

        recognition_result

    ) -> CustomerRequest:

        customer = Customer(

            name=recognition_result.metadata.company,

            language=recognition_result.metadata.language,

            email=recognition_result.metadata.sender_email

        )

        request = CustomerRequest(

            customer=customer,

            language=recognition_result.metadata.language

        )

        request.products.append(

            ProductRequest(

                category="window",

                quantity=8

            )

        )

        return request